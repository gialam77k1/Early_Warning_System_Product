import os
import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime
from django.core.management.base import BaseCommand
from core.models import BangDiem
from ml.mlflow_manager import MLflowManager
from ml.train_model import FEATURE_COLUMNS, TARGET_COLUMN, LABEL_ORDER, get_models, evaluate_model
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import mlflow

from ml.drift_detection import check_drift

# Ngưỡng tối thiểu bản ghi mới để tiến hành retrain
MIN_NEW_RECORDS = 20
# Ngưỡng F1 an toàn tối thiểu
SAFETY_THRESHOLD = 0.75

class Command(BaseCommand):
    help = 'Retrain ML model using COMBINED old + new data, track with MLflow'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- BẮT ĐẦU QUY TRÌNH MLOPS PIPELINE ---'))

        # ── BƯỚC 1: Load dữ liệu gốc (training dataset) ──────────────────
        BASE_DIR = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        ref_path = os.path.join(BASE_DIR, '..', 'data_train', 'train_dataset.csv')

        if not os.path.exists(ref_path):
            self.stdout.write(self.style.ERROR(f'Không tìm thấy file dữ liệu gốc: {ref_path}'))
            return

        df_original = pd.read_csv(ref_path)
        self.stdout.write(f'Đã load {len(df_original)} bản ghi từ dữ liệu gốc (train_dataset.csv).')

        # ── BƯỚC 2: Load dữ liệu mới từ Database ─────────────────────────
        queryset = BangDiem.objects.exclude(performance_label='').exclude(performance_label=None)
        new_count = queryset.count()

        self.stdout.write(f'Tìm thấy {new_count} bản ghi mới trong Database.')

        if new_count < MIN_NEW_RECORDS:
            self.stdout.write(self.style.WARNING(
                f'Dữ liệu mới chưa đủ ({new_count}/{MIN_NEW_RECORDS}). '
                f'Bỏ qua retraining, giữ nguyên model hiện tại.'
            ))
            return

        data = []
        for obj in queryset:
            row = obj.get_features()
            row[TARGET_COLUMN] = obj.performance_label
            data.append(row)

        df_new = pd.DataFrame(data)
        self.stdout.write(f'Đã load {len(df_new)} bản ghi mới từ Database.')

        # ── BƯỚC 3: Kiểm tra Data Drift ──────────────────────────────────
        self.stdout.write('Đang kiểm tra Data Drift...')
        drift_results = check_drift(df_original, df_new)
        drift_detected = any(res['has_drift'] for res in drift_results.values())

        if drift_detected:
            self.stdout.write(self.style.WARNING(
                '🚨 PHÁT HIỆN DATA DRIFT! Phân phối dữ liệu mới khác biệt đáng kể.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                '✅ Dữ liệu ổn định, không phát hiện drift đáng kể.'
            ))

        # ── BƯỚC 4: Kết hợp dữ liệu cũ + mới ───────────────────────────
        # Đây là cốt lõi: KHÔNG chỉ train trên dữ liệu mới
        # mà train trên TOÀN BỘ để tránh Catastrophic Forgetting
        df_combined = pd.concat(
            [df_original[FEATURE_COLUMNS + [TARGET_COLUMN]], df_new[FEATURE_COLUMNS + [TARGET_COLUMN]]],
            ignore_index=True
        )
        # Bỏ các hàng có label không hợp lệ
        df_combined = df_combined[df_combined[TARGET_COLUMN].isin(LABEL_ORDER)]

        self.stdout.write(
            f'Tổng dữ liệu kết hợp: {len(df_combined)} bản ghi '
            f'({len(df_original)} gốc + {len(df_new)} mới)'
        )

        # ── BƯỚC 5: Tiền xử lý ───────────────────────────────────────────
        X = df_combined[FEATURE_COLUMNS].values
        le = LabelEncoder()
        le.classes_ = np.array(LABEL_ORDER)
        y = le.transform(df_combined[TARGET_COLUMN].values)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        self.stdout.write(f'Train set: {len(X_train)} | Test set: {len(X_test)}')

        # ── BƯỚC 6: Đánh giá model hiện tại (Champion) ───────────────────
        old_f1 = 0.0
        current_model_path = os.path.join(
            os.path.dirname(BASE_DIR), 'ml', 'saved_models', 'best_model.pkl'
        )
        # Fallback path
        if not os.path.exists(current_model_path):
            current_model_path = os.path.join(BASE_DIR, '..', 'ml', 'saved_models', 'best_model.pkl')

        if os.path.exists(current_model_path):
            try:
                current_model = joblib.load(current_model_path)
                m_old, _, _, _ = evaluate_model(current_model, X_test, y_test, LABEL_ORDER)
                old_f1 = m_old['f1_macro']
                self.stdout.write(self.style.NOTICE(
                    f'📊 Model Champion hiện tại — F1: {old_f1:.4f}'
                ))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Không load được model cũ: {e}'))
        else:
            self.stdout.write(self.style.WARNING('Không tìm thấy model cũ, sẽ chấp nhận model mới nếu đủ ngưỡng an toàn.'))

        # ── BƯỚC 7: Huấn luyện các model Challenger ──────────────────────
        ml_manager = MLflowManager(experiment_name="EWS_Retraining_Pipeline")

        best_f1 = -1
        best_model = None
        best_model_name = ""
        best_metrics = {}

        with ml_manager.start_run(run_name=f"retrain_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):

            # Log thông tin phiên chạy
            mlflow.log_param("original_samples", len(df_original))
            mlflow.log_param("new_samples_from_db", len(df_new))
            mlflow.log_param("total_combined_samples", len(df_combined))
            mlflow.log_param("drift_detected", str(drift_detected))
            mlflow.log_param("old_f1_baseline", round(old_f1, 4))
            mlflow.log_param("min_new_records_threshold", MIN_NEW_RECORDS)
            mlflow.log_param("safety_threshold", SAFETY_THRESHOLD)

            models = get_models()
            for name, model in models.items():
                self.stdout.write(f'  Đang huấn luyện {name} trên {len(X_train)} bản ghi...')
                model.fit(X_train, y_train)
                metrics, _, _, _ = evaluate_model(model, X_test, y_test, LABEL_ORDER)

                self.stdout.write(f'    → F1: {metrics["f1_macro"]:.4f}')

                # Chọn model tốt nhất trong lượt này
                if metrics['f1_macro'] > best_f1:
                    best_f1 = metrics['f1_macro']
                    best_model = model
                    best_model_name = name
                    best_metrics = metrics

            # ── BƯỚC 8: Quyết định Champion vs Challenger ─────────────────
            is_better = best_f1 > old_f1
            is_safe   = best_f1 >= SAFETY_THRESHOLD

            self.stdout.write(
                f'\n🏆 Challenger tốt nhất: {best_model_name} — F1: {best_f1:.4f}'
            )
            self.stdout.write(
                f'   So sánh: {best_f1:.4f} (mới) vs {old_f1:.4f} (cũ) — '
                f'{"✅ Tốt hơn" if is_better else "❌ Không tốt hơn"}'
            )

            if is_better and is_safe:
                self.stdout.write(self.style.SUCCESS(
                    f'✅ CHẤP NHẬN MODEL MỚI! Cải thiện: +{(best_f1 - old_f1) * 100:.2f}%'
                ))

                # Backup model cũ trước khi thay
                if os.path.exists(current_model_path):
                    backup_path = current_model_path.replace(
                        '.pkl', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M")}.pkl'
                    )
                    os.rename(current_model_path, backup_path)
                    self.stdout.write(f'   Đã backup model cũ → {os.path.basename(backup_path)}')

                # Lưu model mới vào production
                joblib.dump(best_model, current_model_path)
                self.stdout.write(f'   Đã lưu model mới → best_model.pkl')

                # Log lên MLflow
                mlflow.log_metrics({
                    'best_f1': best_metrics['f1_macro'],
                    'best_accuracy': best_metrics['accuracy'],
                    'improvement': best_f1 - old_f1,
                })
                mlflow.log_param("winning_model", best_model_name)
                mlflow.log_param("decision", "ACCEPTED")
                ml_manager.log_model(best_model, artifact_path="best_model")

                decision = "ACCEPTED"
                status_msg = f"Model mới ({best_model_name}) thay thế model cũ"

            else:
                reason = "Không vượt ngưỡng an toàn" if not is_safe else "Không tốt hơn model cũ"
                self.stdout.write(self.style.WARNING(
                    f'❌ TỪ CHỐI MODEL MỚI: {reason}. Giữ nguyên model cũ.'
                ))

                mlflow.log_metrics({'best_f1': best_f1, 'old_f1': old_f1})
                mlflow.log_param("decision", "REJECTED")
                mlflow.log_param("rejection_reason", reason)

                decision = "REJECTED"
                status_msg = f"Rejected: {reason}"

            # ── BƯỚC 9: Lưu metadata kết quả ─────────────────────────────
            output_dir = os.path.dirname(current_model_path)
            os.makedirs(output_dir, exist_ok=True)

            retrain_result = {
                'run_time':          datetime.now().isoformat(),
                'original_samples':  len(df_original),
                'new_samples':       len(df_new),
                'total_samples':     len(df_combined),
                'drift_detected':    drift_detected,
                'old_f1':            round(old_f1, 4),
                'new_f1':            round(best_f1, 4),
                'winning_model':     best_model_name,
                'decision':          decision,
                'reason':            status_msg,
            }
            result_path = os.path.join(output_dir, 'last_retrain_result.json')
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(retrain_result, f, indent=4, ensure_ascii=False)

            self.stdout.write(f'   Kết quả đã lưu → {result_path}')

        self.stdout.write(self.style.SUCCESS('--- QUY TRÌNH MLOPS HOÀN TẤT ---'))

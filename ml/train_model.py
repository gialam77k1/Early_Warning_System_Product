import os
import sys
import json
import warnings
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)

warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
DATA_PATH = os.path.join(PROJECT_DIR, 'data_train', 'train_dataset.csv')
MODEL_OUTPUT_DIR = os.path.join(BASE_DIR, 'saved_models')
REPORT_OUTPUT_DIR = os.path.join(BASE_DIR, 'reports')

# final_exam bị loại khỏi features vì chỉ có SAU khi thi xong
# Early Warning phải dự đoán TRƯỚC khi thi cuối kỳ
FEATURE_COLUMNS = [
    'homework_1', 'homework_2', 'homework_3',
    'quiz_1', 'quiz_2',
    'midterm_score',
    'attendance_rate'
]
TARGET_COLUMN = 'performance_label'
LABEL_ORDER = ['Weak', 'Average', 'Good', 'Excellent']

TEST_SIZE = 0.2
RANDOM_STATE = 42


def create_dirs():
    """Tạo các thư mục cần thiết"""
    os.makedirs(MODEL_OUTPUT_DIR, exist_ok=True)
    os.makedirs(REPORT_OUTPUT_DIR, exist_ok=True)
    print("Đã tạo thư mục output")


def load_data():
    """Đọc và kiểm tra dữ liệu"""
    print("\n" + "="*60)
    print(" BƯỚC 1: ĐỌC DỮ LIỆU")
    print("="*60)
    
    df = pd.read_csv(DATA_PATH)
    
    print(f" File: {DATA_PATH}")
    print(f" Kích thước: {df.shape[0]} hàng x {df.shape[1]} cột")
    print(f"\n Các cột: {list(df.columns)}")
    print(f"\n Thống kê cơ bản:")
    print(df[FEATURE_COLUMNS].describe().round(2).to_string())
    
    print(f"\n Phân bố label ({TARGET_COLUMN}):")
    label_counts = df[TARGET_COLUMN].value_counts()
    for label in LABEL_ORDER:
        count = label_counts.get(label, 0)
        pct = count / len(df) * 100
        print(f"   {label:12s}: {count:5d} ({pct:.1f}%)")
    
    missing = df[FEATURE_COLUMNS + [TARGET_COLUMN]].isnull().sum()
    if missing.sum() > 0:
        print(f"\n Missing values:\n{missing[missing > 0]}")
    else:
        print(f"\n Không có missing values")
    
    return df


def prepare_data(df):
    """Chuẩn bị X, y cho training"""
    print("\n" + "="*60)
    print(" BƯỚC 2: CHUẨN BỊ DỮ LIỆU")
    print("="*60)
    
    X = df[FEATURE_COLUMNS].values
    
    le = LabelEncoder()
    le.classes_ = np.array(LABEL_ORDER)
    y = le.transform(df[TARGET_COLUMN].values)
    
    print(f" Features shape: {X.shape}")
    print(f" Labels encoded: {dict(zip(LABEL_ORDER, range(len(LABEL_ORDER))))}")
   
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    
    print(f" Train set: {X_train.shape[0]} samples")
    print(f" Test set:  {X_test.shape[0]} samples")
    
    return X_train, X_test, y_train, y_test, le


def get_models():
    models = {
        'Random Forest': RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=RANDOM_STATE,
            n_jobs=-1
        ),
        'Logistic Regression': LogisticRegression(
            max_iter=1000,
            multi_class='multinomial',
            solver='lbfgs',
            random_state=RANDOM_STATE
        ),
        'XGBoost': XGBClassifier(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.1,
            random_state=RANDOM_STATE,
            use_label_encoder=False,
            eval_metric='mlogloss'
        )
    }
    return models


def evaluate_model(model, X_test, y_test, label_names):
    """Đánh giá model trên test set"""
    y_pred = model.predict(X_test)
    
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision_macro': precision_score(y_test, y_pred, average='macro', zero_division=0),
        'recall_macro': recall_score(y_test, y_pred, average='macro', zero_division=0),
        'f1_macro': f1_score(y_test, y_pred, average='macro', zero_division=0),
        'precision_weighted': precision_score(y_test, y_pred, average='weighted', zero_division=0),
        'recall_weighted': recall_score(y_test, y_pred, average='weighted', zero_division=0),
        'f1_weighted': f1_score(y_test, y_pred, average='weighted', zero_division=0),
    }
    
    report = classification_report(y_test, y_pred, target_names=label_names, zero_division=0)
    cm = confusion_matrix(y_test, y_pred)
    
    return metrics, report, cm, y_pred


def train_all_models(X_train, X_test, y_train, y_test, le):
    """Train và đánh giá tất cả models"""
    print("\n" + "="*60)
    print(" BƯỚC 3: TRAIN & ĐÁNH GIÁ MODELS")
    print("="*60)
    
    models = get_models()
    results = {}
    
    for name, model in models.items():
        print(f"\n{'─'*50}")
        print(f" Training: {name}...")
        
        model.fit(X_train, y_train)
        
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
        cv_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring='f1_macro')
        
        metrics, report, cm, y_pred = evaluate_model(model, X_test, y_test, le.classes_)
        
        results[name] = {
            'model': model,
            'metrics': metrics,
            'report': report,
            'confusion_matrix': cm,
            'cv_scores': cv_scores,
            'y_pred': y_pred
        }
        
        print(f" {name} - Kết quả:")
        print(f"   Accuracy:          {metrics['accuracy']:.4f}")
        print(f"   F1-score (macro):  {metrics['f1_macro']:.4f}")
        print(f"   F1-score (weighted): {metrics['f1_weighted']:.4f}")
        print(f"   CV F1 (5-fold):    {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        print(f"\n Classification Report:\n{report}")
    
    return results


def select_best_model(results):
    """Chọn model tốt nhất dựa trên F1-score macro"""
    print("\n" + "="*60)
    print(" BƯỚC 4: SO SÁNH & CHỌN MODEL TỐT NHẤT")
    print("="*60)
    
    comparison = []
    for name, result in results.items():
        m = result['metrics']
        cv = result['cv_scores']
        comparison.append({
            'Model': name,
            'Accuracy': m['accuracy'],
            'Precision': m['precision_macro'],
            'Recall': m['recall_macro'],
            'F1 (macro)': m['f1_macro'],
            'F1 (weighted)': m['f1_weighted'],
            'CV F1 Mean': cv.mean(),
            'CV F1 Std': cv.std()
        })
    
    df_compare = pd.DataFrame(comparison)
    print("\n Bảng so sánh:")
    print(df_compare.to_string(index=False, float_format='%.4f'))
    
    best_name = df_compare.loc[df_compare['F1 (macro)'].idxmax(), 'Model']
    print(f"\n🏆 Model tốt nhất: **{best_name}** (F1 macro = {results[best_name]['metrics']['f1_macro']:.4f})")
    
    return best_name, df_compare


def plot_confusion_matrices(results, le):
    """Vẽ confusion matrix cho tất cả models"""
    print("\n Đang tạo biểu đồ Confusion Matrix...")
    
    fig, axes = plt.subplots(1, 3, figsize=(20, 5))
    fig.suptitle('Confusion Matrix - So sánh 3 Models', fontsize=16, fontweight='bold')
    
    for idx, (name, result) in enumerate(results.items()):
        cm = result['confusion_matrix']
        sns.heatmap(
            cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=le.classes_, yticklabels=le.classes_,
            ax=axes[idx]
        )
        axes[idx].set_title(f'{name}\n(F1={result["metrics"]["f1_macro"]:.3f})', fontsize=12)
        axes[idx].set_xlabel('Predicted')
        axes[idx].set_ylabel('Actual')
    
    plt.tight_layout()
    path = os.path.join(REPORT_OUTPUT_DIR, 'confusion_matrices.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f" Đã lưu: {path}")


def plot_feature_importance(model, feature_names, model_name):
    """Vẽ biểu đồ Feature Importance"""
    print(" Đang tạo biểu đồ Feature Importance...")
    
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
    else:
        print(" Model không hỗ trợ feature_importances_")
        return
    
    indices = np.argsort(importances)[::-1]
    sorted_features = [feature_names[i] for i in indices]
    sorted_importances = importances[indices]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = sns.color_palette('viridis', len(sorted_features))
    bars = ax.barh(range(len(sorted_features)), sorted_importances, color=colors)
    ax.set_yticks(range(len(sorted_features)))
    ax.set_yticklabels(sorted_features, fontsize=12)
    ax.set_xlabel('Importance', fontsize=12)
    ax.set_title(f'Feature Importance - {model_name}', fontsize=14, fontweight='bold')
    ax.invert_yaxis()
    
    for bar, val in zip(bars, sorted_importances):
        ax.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height()/2,
                f'{val:.3f}', va='center', fontsize=10)
    
    plt.tight_layout()
    path = os.path.join(REPORT_OUTPUT_DIR, 'feature_importance.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f" Đã lưu: {path}")
    
    print(f"\n Feature Importance ({model_name}):")
    for feat, imp in zip(sorted_features, sorted_importances):
        bar = '' * int(imp * 50)
        print(f"   {feat:18s}: {imp:.4f} {bar}")


def plot_model_comparison(df_compare):
    print(" Đang tạo biểu đồ so sánh models...")
    
    metrics_to_plot = ['Accuracy', 'Precision', 'Recall', 'F1 (macro)']
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(metrics_to_plot))
    width = 0.25
    colors = ['#2196F3', '#FF9800', '#4CAF50']
    
    for idx, (_, row) in enumerate(df_compare.iterrows()):
        values = [row[m] for m in metrics_to_plot]
        bars = ax.bar(x + idx * width, values, width, 
                      label=row['Model'], color=colors[idx], alpha=0.85)

        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                    f'{val:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    ax.set_xlabel('Metrics', fontsize=12)
    ax.set_ylabel('Score', fontsize=12)
    ax.set_title('So sánh hiệu suất 3 Models', fontsize=14, fontweight='bold')
    ax.set_xticks(x + width)
    ax.set_xticklabels(metrics_to_plot, fontsize=11)
    ax.set_ylim(0, 1.1)
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    path = os.path.join(REPORT_OUTPUT_DIR, 'model_comparison.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f" Đã lưu: {path}")


def plot_label_distribution(df):
    print(" Đang tạo biểu đồ phân bố label...")
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    label_counts = df[TARGET_COLUMN].value_counts().reindex(LABEL_ORDER)
    colors = ['#f44336', '#ff9800', '#2196f3', '#4caf50']
    
    axes[0].bar(label_counts.index, label_counts.values, color=colors, alpha=0.85)
    axes[0].set_title('Phân bố Performance Label', fontsize=13, fontweight='bold')
    axes[0].set_xlabel('Label')
    axes[0].set_ylabel('Số lượng')
    for i, (label, count) in enumerate(label_counts.items()):
        axes[0].text(i, count + 20, str(count), ha='center', fontweight='bold')
    
    axes[1].pie(label_counts.values, labels=label_counts.index, colors=colors,
                autopct='%1.1f%%', startangle=90, textprops={'fontsize': 11})
    axes[1].set_title('Tỷ lệ phần trăm', fontsize=13, fontweight='bold')
    
    plt.tight_layout()
    path = os.path.join(REPORT_OUTPUT_DIR, 'label_distribution.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f" Đã lưu: {path}")


def save_best_model(results, best_name, le):
    print("\n" + "="*60)
    print(" BƯỚC 5: LƯU MODEL")
    print("="*60)
    
    best_model = results[best_name]['model']
    best_metrics = results[best_name]['metrics']
    
    model_path = os.path.join(MODEL_OUTPUT_DIR, 'best_model.pkl')
    joblib.dump(best_model, model_path)
    print(f" Model đã lưu: {model_path}")
    
    le_path = os.path.join(MODEL_OUTPUT_DIR, 'label_encoder.pkl')
    joblib.dump(le, le_path)
    print(f" Label Encoder đã lưu: {le_path}")
    
    metadata = {
        'model_name': best_name,
        'model_file': 'best_model.pkl',
        'label_encoder_file': 'label_encoder.pkl',
        'feature_columns': FEATURE_COLUMNS,
        'label_order': LABEL_ORDER,
        'target_column': TARGET_COLUMN,
        'metrics': {k: round(v, 4) for k, v in best_metrics.items()},
        'cv_f1_mean': round(results[best_name]['cv_scores'].mean(), 4),
        'cv_f1_std': round(results[best_name]['cv_scores'].std(), 4),
        'test_size': TEST_SIZE,
        'random_state': RANDOM_STATE,
        'description': 'Early Warning System - Dự đoán mức độ học tập học viên'
    }
    
    metadata_path = os.path.join(MODEL_OUTPUT_DIR, 'model_metadata.json')
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f" Metadata đã lưu: {metadata_path}")
    
    for name, result in results.items():
        safe_name = name.lower().replace(' ', '_')
        path = os.path.join(MODEL_OUTPUT_DIR, f'{safe_name}.pkl')
        joblib.dump(result['model'], path)
        print(f"   📦 {name}: {path}")
    
    return model_path


def save_report(results, best_name, df_compare):
    print("\n Đang lưu báo cáo...")
    
    report_path = os.path.join(REPORT_OUTPUT_DIR, 'evaluation_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("  EARLY WARNING SYSTEM - BÁO CÁO ĐÁNH GIÁ MODEL\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(" BẢNG SO SÁNH MODELS:\n")
        f.write(df_compare.to_string(index=False, float_format='%.4f'))
        f.write("\n\n")
        
        f.write(f" MODEL TỐT NHẤT: {best_name}\n")
        f.write(f"   F1-score (macro): {results[best_name]['metrics']['f1_macro']:.4f}\n\n")
        
        for name, result in results.items():
            f.write(f"\n{'─' * 50}\n")
            f.write(f"📋 {name} - Classification Report:\n")
            f.write(result['report'])
            f.write(f"\nCV F1 (5-fold): {result['cv_scores'].mean():.4f} ± {result['cv_scores'].std():.4f}\n")
    
    print(f" Báo cáo đã lưu: {report_path}")

def main():
    print(" EARLY WARNING SYSTEM - MODEL TRAINING PIPELINE")
    print("=" * 60)
    
    create_dirs()
    
    df = load_data()
    
    X_train, X_test, y_train, y_test, le = prepare_data(df)
    
    results = train_all_models(X_train, X_test, y_train, y_test, le)
    
    best_name, df_compare = select_best_model(results)
    
    print("\n" + "="*60)
    print(" ĐANG TẠO BIỂU ĐỒ...")
    print("="*60)
    
    plot_label_distribution(df)
    plot_confusion_matrices(results, le)
    plot_feature_importance(results[best_name]['model'], FEATURE_COLUMNS, best_name)
    plot_model_comparison(df_compare)
    
    model_path = save_best_model(results, best_name, le)
    
    save_report(results, best_name, df_compare)
    
    print("\n" + "="*60)
    print(" TRAINING HOÀN TẤT!")
    print("="*60)
    print(f" Best Model:  {best_name}")
    print(f" Accuracy:    {results[best_name]['metrics']['accuracy']:.4f}")
    print(f" F1 (macro):  {results[best_name]['metrics']['f1_macro']:.4f}")
    print(f" Model file:  {model_path}")
    print(f" Reports:     {REPORT_OUTPUT_DIR}")
    print(f"\n Output files:")
    print(f"   ml/saved_models/best_model.pkl")
    print(f"   ml/saved_models/label_encoder.pkl")
    print(f"   ml/saved_models/model_metadata.json")
    print(f"   ml/reports/confusion_matrices.png")
    print(f"   ml/reports/feature_importance.png")
    print(f"   ml/reports/model_comparison.png")
    print(f"   ml/reports/label_distribution.png")
    print(f"   ml/reports/evaluation_report.txt")


if __name__ == '__main__':
    main()

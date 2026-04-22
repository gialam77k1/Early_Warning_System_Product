"""
=============================================================
  Early Warning System - Prediction Module
  Load model đã train và dự đoán kết quả học tập
=============================================================
"""

import os
import json
import joblib
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'saved_models')


class StudentPredictor:
    """
    Class dự đoán mức độ học tập của học viên
    
    Usage:
        predictor = StudentPredictor()
        
        # Dự đoán 1 học viên
        result = predictor.predict_single(
            homework_1=8.0, homework_2=7.5, homework_3=8.0,
            quiz_1=7.0, quiz_2=8.0,
            midterm_score=7.5, final_exam=8.0,
            attendance_rate=0.9
        )
        print(result)
        # {'predicted_label': 'Good', 'probabilities': {'Weak': 0.02, 'Average': 0.15, 'Good': 0.63, 'Excellent': 0.20}}
    """
    
    def __init__(self, model_path=None):
        """Load model và metadata"""
        if model_path is None:
            model_path = os.path.join(MODEL_DIR, 'best_model.pkl')
        
        le_path = os.path.join(MODEL_DIR, 'label_encoder.pkl')
        metadata_path = os.path.join(MODEL_DIR, 'model_metadata.json')
        
        # Check files exist
        for path, name in [(model_path, 'Model'), (le_path, 'Label Encoder'), (metadata_path, 'Metadata')]:
            if not os.path.exists(path):
                raise FileNotFoundError(f"❌ {name} không tìm thấy: {path}\n   Hãy chạy train_model.py trước!")
        
        self.model = joblib.load(model_path)
        self.label_encoder = joblib.load(le_path)
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        
        self.feature_columns = self.metadata['feature_columns']
        self.label_order = self.metadata['label_order']
        
        print(f"✅ Loaded model: {self.metadata['model_name']}")
        print(f"   F1-score: {self.metadata['metrics']['f1_macro']}")
    
    def predict_single(self, homework_1, homework_2, homework_3,
                       quiz_1, quiz_2, midterm_score,
                       attendance_rate, **kwargs):
        """
        Dự đoán mức độ học tập cho 1 học viên.
        Các feature chỉ bao gồm điểm có TRƯỚC khi thi cuối kỳ.
        final_exam được bỏ qua (đưa qua **kwargs) vì nó là kết quả cần dự đoán.
        
        Returns:
            dict: {
                'predicted_label': str,  # Weak/Average/Good/Excellent
                'probabilities': dict,   # Xác suất từng label
                'risk_score': float      # Điểm rủi ro dự kiến (không có final_exam)
            }
        """
        features = np.array([[
            homework_1, homework_2, homework_3,
            quiz_1, quiz_2,
            midterm_score,
            attendance_rate
        ]])
        
        # Predict
        pred_encoded = self.model.predict(features)[0]
        pred_label = self.label_order[pred_encoded]
        
        # Probabilities
        proba = self.model.predict_proba(features)[0]
        prob_dict = {label: round(float(p), 4) for label, p in zip(self.label_order, proba)}
        
        # Điểm rủi ro dự kiến (dựa trên dữ liệu hiện có, không có final_exam)
        homework_avg = np.mean([homework_1, homework_2, homework_3])
        quiz_avg = np.mean([quiz_1, quiz_2])
        mid_contribution = round(
            0.25 * homework_avg + 0.30 * quiz_avg + 0.45 * midterm_score,
            2
        )
        
        return {
            'predicted_label': pred_label,
            'probabilities': prob_dict,
            'final_score': mid_contribution   # Đây là điểm ước lượng, không phải điểm thật
        }
    
    def predict_batch(self, data_list):
        """
        Dự đoán cho nhiều học viên
        
        Args:
            data_list: list of dict, mỗi dict chứa 8 features
            
        Returns:
            list of dict: kết quả dự đoán cho mỗi học viên
        """
        results = []
        for data in data_list:
            result = self.predict_single(**data)
            results.append(result)
        return results
    
    def get_risk_level(self, predicted_label):
        """
        Đánh giá mức độ rủi ro
        
        Returns:
            str: 'high_risk' / 'medium_risk' / 'low_risk' / 'no_risk'
        """
        risk_map = {
            'Weak': 'high_risk',
            'Average': 'medium_risk',
            'Good': 'low_risk',
            'Excellent': 'no_risk'
        }
        return risk_map.get(predicted_label, 'unknown')


# ============================================================
# Quick test
# ============================================================
if __name__ == '__main__':
    print("🔮 EARLY WARNING SYSTEM - PREDICTION TEST")
    print("=" * 50)
    
    predictor = StudentPredictor()
    
    # Test cases
    test_students = [
        {
            'name': 'Học viên A (Giỏi)',
            'data': dict(homework_1=8.5, homework_2=9.0, homework_3=8.5,
                        quiz_1=8.0, quiz_2=9.0, midterm_score=8.5,
                        final_exam=9.0, attendance_rate=0.95)
        },
        {
            'name': 'Học viên B (Trung bình)',
            'data': dict(homework_1=5.5, homework_2=6.0, homework_3=5.0,
                        quiz_1=5.0, quiz_2=6.0, midterm_score=5.5,
                        final_exam=5.0, attendance_rate=0.7)
        },
        {
            'name': 'Học viên C (Yếu - CẦN CẢNH BÁO)',
            'data': dict(homework_1=3.0, homework_2=2.5, homework_3=3.5,
                        quiz_1=2.0, quiz_2=3.0, midterm_score=3.0,
                        final_exam=2.5, attendance_rate=0.4)
        },
    ]
    
    for student in test_students:
        print(f"\n{'─'*50}")
        print(f"👤 {student['name']}")
        result = predictor.predict_single(**student['data'])
        risk = predictor.get_risk_level(result['predicted_label'])
        
        print(f"   🏷️ Dự đoán:    {result['predicted_label']}")
        print(f"   📊 Final Score: {result['final_score']}")
        print(f"   ⚠️ Mức rủi ro: {risk}")
        print(f"   📈 Xác suất:")
        for label, prob in result['probabilities'].items():
            bar = '█' * int(prob * 30)
            print(f"      {label:12s}: {prob:.2%} {bar}")

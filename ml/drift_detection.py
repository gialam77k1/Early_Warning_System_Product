import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
import os

def check_drift(reference_data, current_data, threshold=0.05):
    """
    Kiểm tra Data Drift sử dụng Kolmogorov-Smirnov test.
    reference_data: Dữ liệu huấn luyện ban đầu (DataFrame)
    current_data: Dữ liệu thực tế từ Database (DataFrame)
    """
    drift_results = {}
    
    # Chỉ kiểm tra trên các feature columns
    features = [col for col in reference_data.columns if col in current_data.columns]
    
    for feature in features:
        # KS Test: p-value < threshold => phân phối khác nhau (có drift)
        statistic, p_value = ks_2samp(reference_data[feature], current_data[feature])
        has_drift = p_value < threshold
        drift_results[feature] = {
            'p_value': p_value,
            'has_drift': has_drift,
            'ks_statistic': statistic
        }
        
    return drift_results

if __name__ == "__main__":
    # Test thử
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ref_path = os.path.join(os.path.dirname(BASE_DIR), 'data_train', 'train_dataset.csv')
    
    if os.path.exists(ref_path):
        df_ref = pd.read_csv(ref_path)
        # Giả lập dữ liệu current
        df_curr = df_ref.sample(100).copy()
        df_curr['attendance_rate'] = df_curr['attendance_rate'] * 0.5 # Gây drift giả
        
        results = check_drift(df_ref, df_curr)
        for feat, res in results.items():
            status = "🚨 DRIFT DETECTED" if res['has_drift'] else "✅ Stable"
            print(f"{feat:18s}: {status} (p-value: {res['p_value']:.4f})")

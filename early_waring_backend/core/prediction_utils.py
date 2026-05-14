import json
import os
import sys

from django.conf import settings

from .models import BangDiem, DuDoanML


def _get_ml_dir():
    return os.path.abspath(os.path.join(settings.BASE_DIR, '..', 'ml'))


def _get_model_metadata_path():
    return os.path.join(_get_ml_dir(), 'saved_models', 'model_metadata.json')


def load_predictor():
    ml_dir = _get_ml_dir()
    if ml_dir not in sys.path:
        sys.path.insert(0, ml_dir)
    from predict import StudentPredictor
    return StudentPredictor()


def get_model_name():
    try:
        with open(_get_model_metadata_path(), 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        return metadata.get('model_name', 'Unknown')
    except Exception:
        return 'Unknown'


def upsert_prediction_for_score(bang_diem, predictor=None, model_name=None):
    if not bang_diem.has_complete_prediction_inputs():
        return None, False

    predictor = predictor or load_predictor()
    model_name = model_name or get_model_name()

    result = predictor.predict_single(**bang_diem.get_features())
    probabilities = result.get('probabilities', {})
    du_doan, created = DuDoanML.objects.update_or_create(
        bang_diem=bang_diem,
        defaults={
            'predicted_label': result['predicted_label'],
            'prob_weak': probabilities.get('Weak', 0),
            'prob_average': probabilities.get('Average', 0),
            'prob_good': probabilities.get('Good', 0),
            'prob_excellent': probabilities.get('Excellent', 0),
            'model_name': model_name,
        }
    )
    return du_doan, created


def backfill_predictions_for_scores(score_queryset=None, only_approved=False):
    queryset = score_queryset if score_queryset is not None else BangDiem.objects.all()
    if only_approved:
        queryset = queryset.filter(is_approved=True)

    scores = list(
        queryset.filter(
            homework_1__isnull=False,
            homework_2__isnull=False,
            homework_3__isnull=False,
            quiz_1__isnull=False,
            quiz_2__isnull=False,
            midterm_score__isnull=False,
            attendance_rate__isnull=False,
        ).select_related('hoc_vien', 'hoc_vien__nguoi_dung', 'hoc_vien__lop').order_by('id')
    )
    if not scores:
        return {
            'processed': 0,
            'created': 0,
            'updated': 0,
        }

    predictor = load_predictor()
    model_name = get_model_name()
    created_count = 0
    updated_count = 0

    for score in scores:
        _, created = upsert_prediction_for_score(score, predictor=predictor, model_name=model_name)
        if created:
            created_count += 1
        else:
            updated_count += 1

    return {
        'processed': len(scores),
        'created': created_count,
        'updated': updated_count,
    }

mkdir -p models/processor
python -c "
from colpali_engine.models import ColPali, ColPaliProcessor;
ColPali.from_pretrained('vidore/colpali-v1.3').save_pretrained('models/model');
ColPaliProcessor.from_pretrained('vidore/colpaligemma-3b-pt-448-base').save_pretrained('models/processor')"

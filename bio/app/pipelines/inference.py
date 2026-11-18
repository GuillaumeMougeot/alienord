from core.domain.pipeline.pipeline_factory import PipelineFactory
from core.domain.pipeline.entities import Pipeline

class InferencePipelineFactory(PipelineFactory):
    
    def make() -> Pipeline:
        pass
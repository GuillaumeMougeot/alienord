from core.domain.pipeline.entities import Element
from core.infra.adapters.pipeline.pyds.pipeline_builder import PipelineBuilderAdapter as PipelineBuilder

from typing import List

class PipelineBuilderAdapter(PipelineBuilder):
    
    def make_input_elements_for_camera(self, name: str) -> List[Element]:
        """
        Make the necessary input elements from a given camera.
        
        Returns
        -------
        A list of Elements.
        """
        aravissrc = self.make_simple('aravissrc', ('camera-name', name), name=name)
        bayer_capsfilter = self.make_capsfilter(
            video='x-bayer', 
            format='rggb', 
            nvmm=False 
        )
        bayer2rgb = self.make_simple('bayer2rgb')

        nvvideoconvert = self.make_videoconvert(name=f'nvmm-convert-{name}')
        nv_capsfilter = self.make_capsfilter()
        
        elements = [
            aravissrc,
            bayer_capsfilter,
            bayer2rgb,
            nvvideoconvert,
            nv_capsfilter
        ]

        self.link_many(*elements)
        
        return elements


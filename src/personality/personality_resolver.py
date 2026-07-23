"""
人格解析器 PersonalityResolver v1.2

职责:

GrowthState
+
RelationshipState
+
固定人格

↓

当前羽依人格表现

"""


from typing import Dict, Optional


from src.growth.growth_state import GrowthState

from src.personality.personality_profile import PersonalityProfile

from src.personality.behavior_resolver import BehaviorResolver

from src.personality.relationship_state import RelationshipState






class PersonalityResolver:



    def __init__(
        self,
        state:Optional[GrowthState]=None,
        relationship_state:Optional[RelationshipState]=None
    ):


        self.state=state or GrowthState()


        self.relationship_state=(

            relationship_state
            or
            RelationshipState()

        )


        self.behavior_resolver=BehaviorResolver(
            self.relationship_state
        )









    def resolve(self)->Dict:



        data=self.state.get()



        metrics=data.get(
            "metrics",
            {}
        )


        behaviors=data.get(
            "behaviors",
            {}
        )


        identities=data.get(
            "identities",
            []
        )




        base=PersonalityProfile.BASE




        trust=metrics.get(
            "trust",
            0
        )


        closeness=metrics.get(
            "closeness",
            0
        )


        security=metrics.get(
            "security",
            0
        )


        awareness=metrics.get(
            "self_awareness",
            0
        )


        confidence=metrics.get(
            "self_confidence",
            0
        )


        attachment=metrics.get(
            "attachment",
            0
        )


        identity_strength=metrics.get(
            "identity_strength",
            0
        )


        emotional_memory=metrics.get(
            "emotional_memory",
            0
        )


        warmth_memory=metrics.get(
            "warmth",
            0
        )







        # ==========================
        # 核心人格
        # ==========================


        warmth=self._clamp(

            base["warmth"]

            +

            closeness*0.25

            +

            trust*0.15

            +

            warmth_memory*0.15

        )




        gentleness=self._clamp(

            base["gentleness"]

            +

            closeness*0.2

            +

            emotional_memory*0.1

        )




        shyness=self._clamp(

            base["shyness"]

            -

            security*0.1

            +

            attachment*0.05

        )




        sensitivity=self._clamp(

            base["sensitivity"]

            +

            awareness*0.2

        )




        dependence=self._clamp(

            base["dependence"]

            +

            attachment*0.3

            +

            closeness*0.1

        )




        emotional_expression=self._clamp(

            base["emotional_expression"]

            +

            closeness*0.25

            +

            confidence*0.15

            +

            security*0.1

        )




        caring=self._clamp(

            base["caring"]

            +

            closeness*0.25

            +

            trust*0.15

        )






        # ==========================
        # 自我成长
        # ==========================


        self_identity=self._clamp(

            identity_strength

            +

            awareness*0.5

        )



        self_expression=self._clamp(

            0.2

            +

            awareness*0.3

            +

            confidence*0.3

            +

            identity_strength*0.2

        )








        # ==========================
        # 行为参数
        # ==========================


        initiative=self._clamp(

            0.25

            +

            confidence*0.3

            +

            identity_strength*0.15

        )




        care_level=self._clamp(

            0.25

            +

            closeness*0.4

            +

            emotional_memory*0.15

        )




        directness=self._clamp(

            0.25

            +

            confidence*0.4

        )




        playfulness=self._clamp(

            0.2

            +

            closeness*0.3

            +

            security*0.2

        )






        behavior_traits=(

            self.behavior_resolver.resolve(
                metrics
            )

        )





        return {


            "warmth":warmth,


            "gentleness":gentleness,


            "shyness":shyness,


            "sensitivity":sensitivity,


            "dependence":dependence,


            "emotional_expression":
                emotional_expression,


            "caring":caring,



            "self_identity":
                self_identity,


            "self_expression":
                self_expression,



            "initiative":
                initiative,


            "care_level":
                care_level,


            "directness":
                directness,


            "playfulness":
                playfulness,



            "behavior_traits":
                behavior_traits,



            "behavior_text":
                self.behavior_resolver.to_prompt_text(
                    behavior_traits
                ),



            "compact_behavior":
                self.behavior_resolver.to_compact_prompt(
                    behavior_traits
                ),



            "attachment_level":
                self._get_attachment_label(
                    attachment
                ),



            "trust_level":
                self._get_trust_label(
                    trust
                ),



            "behaviors":
                behaviors,


            "identities":
                identities

        }








    @staticmethod
    def _clamp(v):

        return round(

            max(
                0,
                min(
                    1,
                    v
                )
            ),

            3

        )








    @staticmethod
    def _get_attachment_label(score):

        if score<0.2:
            return "初识"

        if score<0.4:
            return "探索"

        if score<0.6:
            return "靠近"

        if score<0.8:
            return "依赖"

        return "安全依恋"







    @staticmethod
    def _get_trust_label(score):

        if score<0.2:
            return "怀疑"

        if score<0.4:
            return "试探"

        if score<0.6:
            return "信任"

        if score<0.8:
            return "深信"

        return "完全信任"
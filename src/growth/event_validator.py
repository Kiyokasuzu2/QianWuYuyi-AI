"""
EventValidator

浅雾羽依成长系统 v1.0

职责:

判断事件是否值得成为羽依人生经历


核心:

过滤普通聊天

保留:

- 自我认知变化
- 与清清关系变化
- 人格形成
- 长期成长
- 重要回忆


输出:

keep:
    进入成长系统


review:
    保存观察，不触发成长


discard:
    丢弃


"""


from typing import List, Dict



IGNORE_KEYWORDS = [

    "你好",
    "在吗",
    "早上好",
    "晚上好",
    "晚安",

]



TECH_KEYWORDS=[

    "安装",
    "配置",
    "部署",
    "报错",
    "日志",
    "代码",
    "插件",
    "运行",
    "启动"
    
]



LIFE_MEANINGS=[

    "birth",
    "identity_creation",
    "relationship_start",
    "promise",
    "growth_support",
    "companionship"

]





class EventValidator:



    def validate(
        self,
        events:List[Dict]
    ):


        result=[]


        for event in events:

            if self.should_keep(event):

                result.append(event)


        return result







    def decide(
        self,
        event:Dict
    ):

        """
        新版决策接口

        return:

        decision,
        score,
        reason

        """



        text=self.build_text(event)



        # 无证据

        if not self.has_evidence(event):

            return (
                "discard",
                0,
                "no_evidence"
            )




        # 普通互动

        for word in IGNORE_KEYWORDS:

            if word in text:

                return (
                    "discard",
                    0.1,
                    "normal_chat"
                )





        # 技术事件

        if self.is_technical(event):


            if self.technical_has_life(event):

                return (

                    "keep",

                    0.8,

                    "technical_with_life"

                )


            return (

                "discard",

                0.2,

                "technical_log"

            )






        score=self.life_value(event)



        if score>=0.65:


            return (

                "keep",

                score,

                "life_event"

            )



        elif score>=0.35:


            return (

                "review",

                score,

                "borderline"

            )



        else:


            return (

                "discard",

                score,

                "low_value"

            )









    def should_keep(
        self,
        event:Dict
    ):


        decision,score,reason=self.decide(event)


        metadata=event.setdefault(
            "metadata",
            {}
        )


        metadata["validator_decision"]=decision


        metadata["validator_score"]=score


        metadata["validator_reason"]=reason



        # review保存，但是禁止成长

        if decision=="review":

            metadata["validator_apply"]=False

            return True



        if decision=="keep":

            metadata["validator_apply"]=True

            return True



        metadata["validator_apply"]=False


        return False







    def build_text(
        self,
        event
    ):


        return (

            event.get(
                "topic",
                ""

            )

            +

            event.get(
                "canonical_topic",
                ""

            )

        ).lower()







    def has_evidence(
        self,
        event
    ):


        return len(

            event.get(
                "evidence",
                []
            )

        )>0








    def evidence_score(
        self,
        event
    ):


        score=0


        evidence=event.get(
            "evidence",
            []
        )


        roles=[

            x.get("role")

            for x in evidence

        ]


        if "user" in roles:

            score+=0.3


        if "assistant" in roles:

            score+=0.3


        if len(evidence)>=2:

            score+=0.2


        if event.get("topic"):

            score+=0.2


        return score







    def is_technical(
        self,
        event
    ):


        text=self.build_text(event)


        return any(

            x in text

            for x in TECH_KEYWORDS

        )







    def technical_has_life(
        self,
        event
    ):


        text=self.build_text(event)


        keywords=[

            "羽依",
            "第一次",
            "诞生",
            "启动",
            "唤醒",
            "人格",
            "身份"

        ]


        return any(

            x in text

            for x in keywords

        )








    def life_value(
        self,
        event
    ):


        score=0


        meaning=event.get(
            "category_id",
            ""
        )


        if meaning in LIFE_MEANINGS:

            score+=0.6



        score += (

            event.get(
                "importance",
                0
            )

            *

            0.2

        )



        score+=self.evidence_score(event)



        text=self.build_text(event)



        if any(

            x in text

            for x in [

                "第一次",
                "首次",
                "初次"

            ]

        ):

            score+=0.2



        return min(
            score,
            1.0
        )
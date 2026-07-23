"""
EventValidator

浅雾羽依成长系统 v0.9


职责:

判断事件是否值得成为:

羽依人生经历


核心:

不是保存发生过的事情

而是保存:

会改变:

- 自我认知
- 与清清关系
- 性格形成
- 成长方向
- 重要回忆


的事件


"""



from typing import List, Dict





# =========================================
# 明确无价值事件
# =========================================


IGNORE_KEYWORDS=[


    "你好",

    "在吗",

    "早上好",

    "晚上好",

    "晚安",


    "测试",

    "test"


]





# =========================================
# 技术事件
# =========================================


TECH_KEYWORDS=[


    "安装",

    "配置",

    "部署",

    "报错",

    "日志",

    "代码",

    "插件",

    "运行"


]








# =========================================
# 人生意义白名单
# =========================================


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

            x.get(
                "role"
            )

            for x in evidence

        ]



        if "user" in roles:

            score+=0.3



        if "assistant" in roles:

            score+=0.3



        if len(evidence)>=2:

            score+=0.2



        if event.get(
            "topic"
        ):

            score+=0.2



        return score









    def is_technical(
        self,
        event
    ):


        text=self.build_text(
            event
        )



        for word in TECH_KEYWORDS:


            if word in text:


                return True



        return False











    def technical_has_life(
        self,
        event
    ):


        text=self.build_text(
            event
        )


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



        importance=event.get(
            "importance",
            0
        )



        score+=importance*0.2



        score+=self.evidence_score(
            event
        )



        text=self.build_text(
            event
        )



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









    def should_keep(
        self,
        event:Dict
    ):



        text=self.build_text(
            event
        )



        # -------------------------
        # 无证据
        # -------------------------


        if not self.has_evidence(
            event
        ):


            print(
                "🗑️无证据:",
                text
            )


            return False







        # -------------------------
        # 普通问候
        # -------------------------


        for word in IGNORE_KEYWORDS:


            if word in text:


                print(
                    "🗑️普通互动:",
                    text
                )


                return False







        # -------------------------
        # 纯技术事件
        # -------------------------


        if self.is_technical(
            event
        ):



            if self.technical_has_life(
                event
            ):


                print(
                    "🌱技术转人生:",
                    text
                )


                return True



            print(
                "🗑️技术日志:",
                text
            )


            return False







        # -------------------------
        # 人生意义判断
        # -------------------------


        score=self.life_value(
            event
        )



        if score>=0.65:


            print(

                f"🌱人生经历:{text} 价值:{score}"

            )


            return True




        print(

            f"🗑️普通事件:{text} 价值:{score}"

        )


        return False
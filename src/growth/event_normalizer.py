"""
事件规范化器（EventNormalizer）

浅雾羽依成长系统 v0.6


职责:

LLM事件
    ↓
标准人生事件


目标:

不是保存聊天记录

而是建立:

羽依人生经历


负责:

- 事件分类
- 人生节点识别
- canonical_topic稳定化
- event_identity稳定识别
- event_id生成
- meaning成长意义
- 重要度
- 情绪标签
- 成长权重

"""



import hashlib

from typing import List, Dict





# =================================================
# 分类规则
# =================================================


CATEGORY_RULES=[



    (
        "羽依诞生阶段",

        [

            "诞生",
            "出生",
            "启动",
            "唤醒",
            "第一次启动",
            "首次启动",
            "初始化",
            "上线"

        ],

        "birth"

    ),




    (
        "身份形成",

        [

            "名字",
            "命名",
            "身份",
            "人格",
            "性格",
            "设定",
            "背景",
            "世界观",
            "形象",
            "创造羽依"

        ],

        "identity_creation"

    ),




    (
        "关系建立",

        [

            "喜欢羽依",
            "喜欢你",
            "我爱你",
            "爱",
            "告白",
            "表白",
            "信任",
            "珍惜"

        ],

        "relationship_start"

    ),




    (
        "承诺",

        [

            "约定",
            "承诺",
            "陪伴",
            "一直陪",
            "未来",
            "永远"

        ],

        "promise"

    ),




    (
        "用户成长",

        [

            "成长",
            "学习",
            "改变",
            "帮助",
            "进步"

        ],

        "growth_support"

    ),




    (
        "记忆强化",

        [

            "第一次",
            "初次",
            "纪念",
            "回忆",
            "珍藏",
            "记住"

        ],

        "companionship"

    )

]








# =================================================
# 唯一人生事件
# =================================================


EVENT_IDENTITY_RULES={



    "yuyi_birth":[

        "诞生",
        "出生",
        "首次启动",
        "第一次启动",
        "首次唤醒"

    ],




    "yuyi_identity":[

        "名字",
        "身份",
        "人格",
        "性格",
        "设定",
        "形象"

    ],




    "first_relationship":[

        "我爱你",
        "第一次告白",
        "表白",
        "喜欢羽依"

    ],




    "companionship_promise":[

        "陪伴",
        "约定",
        "承诺",
        "一直陪"

    ]

}








# =================================================
# 重要度
# =================================================


IMPORTANCE_MAP={


    "birth":0.95,


    "identity_creation":0.95,


    "relationship_start":0.90,


    "promise":0.95,


    "growth_support":0.75,


    "companionship":0.60


}









def make_event_id(
    identity,
    text
):


    if identity:


        return "evt_"+identity



    return (

        "evt_"

        +

        hashlib.md5(

            text.encode(
                "utf-8"
            )

        )
        .hexdigest()[:12]

    )









class EventNormalizer:



    def normalize(
        self,
        events:List[Dict]
    ):


        return [

            self.normalize_one(e)

            for e in events

        ]









    def normalize_one(
        self,
        event
    ):


        topic=event.get(
            "topic",
            ""
        )



        canonical=self.normalize_topic(
            topic
        )



        category,meaning=self.detect_category(
            canonical
        )



        identity=self.detect_identity(
            canonical
        )



        event_type=self.get_event_type(
            meaning
        )



        importance=self.calculate_importance(
            canonical,
            importance=IMPORTANCE_MAP.get(
                meaning,
                0.5
            )
        )



        return {


            "event_id":

                make_event_id(
                    identity,
                    canonical
                ),



            "event_identity":

                identity,



            "topic":

                topic,



            "canonical_topic":

                canonical,



            "category":

                category,



            "category_id":

                meaning,



            "meaning":

                meaning,



            "event_type":

                event_type,



            "event_scope":

                self.detect_scope(
                    meaning
                ),



            "importance":

                importance,



            "growth_weight":

                self.get_growth_weight(
                    identity
                ),



            "emotion_tag":

                self.detect_emotion(
                    canonical
                ),



            "confidence":

                self.confidence(
                    event
                ),



            "source_ids":

                event.get(
                    "source_ids",
                    []
                ),



            "evidence":

                event.get(
                    "evidence",
                    []
                )

        }









    def normalize_topic(
        self,
        topic
    ):


        replacements={


            "配置完成":
                "羽依配置成功",


            "配置成功":
                "羽依配置成功",


            "用户表达爱意":
                "第一次情感表达",


            "情感表达":
                "第一次情感表达",


            "陪伴承诺":
                "长期陪伴约定",


            "羽依诞生的第一天":
                "羽依诞生"

        }



        for a,b in replacements.items():


            if a in topic:


                return b



        return topic.strip()







    def detect_identity(
        self,
        topic
    ):


        for identity,words in EVENT_IDENTITY_RULES.items():


            for w in words:


                if w in topic:


                    return identity



        return None








    def detect_category(
        self,
        topic
    ):


        for category,words,meaning in CATEGORY_RULES:


            for w in words:


                if w in topic:


                    return category,meaning



        return "互动","companionship"








    def get_event_type(
        self,
        meaning
    ):


        mapping={


            "birth":
                "milestone",


            "identity_creation":
                "identity",


            "relationship_start":
                "relationship",


            "promise":
                "commitment",


            "growth_support":
                "growth",


            "companionship":
                "memory"


        }


        return mapping.get(
            meaning,
            "conversation"
        )








    def detect_scope(
        self,
        meaning
    ):


        if meaning in [

            "birth",

            "identity_creation"

        ]:


            return "personality"



        return "relationship"









    def calculate_importance(
        self,
        topic,
        importance
    ):


        bonus=[


            "第一次",

            "首次",

            "初次",

            "长期",

            "约定"

        ]



        for b in bonus:


            if b in topic:


                importance+=0.05



        return min(

            round(
                importance,
                2
            ),

            1.0

        )









    def get_growth_weight(
        self,
        identity
    ):


        values={


            "yuyi_birth":0.9,


            "yuyi_identity":0.95,


            "first_relationship":1.0,


            "companionship_promise":1.0

        }



        return values.get(
            identity,
            0.5
        )









    def detect_emotion(
        self,
        topic
    ):


        if "爱" in topic:

            return [

                "温暖",

                "亲近",

                "感动"

            ]



        if "陪伴" in topic or "约定" in topic:

            return [

                "安心",

                "信赖",

                "依靠"

            ]



        if "诞生" in topic:

            return [

                "新生",

                "期待"

            ]



        if "身份" in topic:

            return [

                "自我",

                "确认"

            ]



        return [

            "经历"

        ]









    def confidence(
        self,
        event
    ):


        score=0


        evidence=len(

            event.get(
                "evidence",
                []
            )

        )


        if evidence>=2:

            score+=0.5


        elif evidence>=1:

            score+=0.3



        if event.get(
            "topic"
        ):

            score+=0.2



        return min(

            round(
                score,
                2
            ),

            1.0

        )
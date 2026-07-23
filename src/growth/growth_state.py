"""
成长状态存储（GrowthState）

浅雾羽依成长系统 v0.5


负责:

保存:

- 羽依人格成长参数
- 人生里程碑
- 成长历史


被:

GrowthEngine

PersonalityResolver

共同使用


"""



import json
import os
from datetime import datetime





STATE_FILE="data/growth_state.json"








DEFAULT_STATE={



    # ======================
    # 人格成长参数
    # ======================


    "metrics":{


        "self_awareness":0.0,


        "identity_strength":0.0,


        "curiosity":0.0,


        "trust":0.0,


        "warmth":0.0,


        "closeness":0.0,


        "attachment":0.0,


        "security":0.0,


        "emotional_memory":0.0,


        "self_confidence":0.0


    },





    # ======================
    # 关键人生节点
    # ======================


    "milestones":[],






    # ======================
    # 成长记录
    # ======================


    "growth_history":[],






    # ======================
    # 更新时间
    # ======================


    "updated_at":None


}









class GrowthState:



    def __init__(
        self
    ):


        self.state={}


        self.load()









    # ======================
    # 加载
    # ======================


    def load(
        self
    ):


        if os.path.exists(
            STATE_FILE
        ):


            try:


                with open(
                    STATE_FILE,
                    "r",
                    encoding="utf-8"
                ) as f:


                    self.state=json.load(
                        f
                    )


                return



            except Exception:


                pass




        self.state=self.default()











    def default(
        self
    ):


        return json.loads(

            json.dumps(
                DEFAULT_STATE
            )

        )











    # ======================
    # 保存
    # ======================


    def save(
        self
    ):


        self.state["updated_at"]=datetime.now().isoformat()



        os.makedirs(

            os.path.dirname(
                STATE_FILE
            ),

            exist_ok=True

        )



        with open(

            STATE_FILE,

            "w",

            encoding="utf-8"

        ) as f:


            json.dump(

                self.state,

                f,

                ensure_ascii=False,

                indent=4

            )











    # ======================
    # 获取全部状态
    # ======================


    def get(
        self
    ):


        return self.state









    # ======================
    # 参数读取
    # ======================


    def get_metric(
        self,
        key
    ):


        return self.state[

            "metrics"

        ].get(

            key,

            0.0

        )











    # ======================
    # 参数增加
    # ======================


    def update_metrics(
        self,
        delta
    ):



        metrics=self.state[

            "metrics"

        ]



        for key,value in delta.items():



            old=metrics.get(

                key,

                0.0

            )



            metrics[key]=round(

                min(

                    old+value,

                    1.0

                ),

                4

            )









    # ======================
    # 里程碑
    # ======================


    def add_milestone(
        self,
        event_id,
        title
    ):



        for item in self.state[

            "milestones"

        ]:


            if item.get(
                "event_id"
            )==event_id:


                return




        self.state[

            "milestones"

        ].append(


            {


                "event_id":

                    event_id,


                "title":

                    title,


                "time":

                    datetime.now().isoformat()


            }


        )









    # ======================
    # 重置
    # ======================


    def reset(
        self
    ):


        self.state=self.default()


        self.save()
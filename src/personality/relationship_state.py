"""
关系状态（RelationshipState） v0.5

浅雾羽依成长系统

职责：

独立管理：

羽依
+
清清

之间的长期关系状态


区别：

GrowthState:
    羽依自身人格成长


RelationshipState:
    羽依如何理解与清清之间的关系



永久数据:
    bond_strength
    trust
    familiarity
    promise_level
    shared_history
    milestones


短期数据:
    activity_level


原则:

重要关系不会遗忘
共同经历会累积
近期活跃度会衰减

"""


import json

from pathlib import Path
from typing import Dict, List

from datetime import datetime, date





class RelationshipState:



    def __init__(
        self,
        state_path="data/relationship_state.json"
    ):


        self.state_path = Path(
            state_path
        )


        self.state_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )


        self._state=self._load()


        self._apply_daily_decay()






    # =========================
    # 存储
    # =========================


    def _load(self):


        if self.state_path.exists():

            try:

                with open(
                    self.state_path,
                    "r",
                    encoding="utf-8"
                ) as f:

                    data=json.load(f)


                    return self._upgrade(
                        data
                    )


            except Exception:

                pass



        return self._default()






    def _save(self):


        self._state["last_updated"]=(
            datetime.now()
            .isoformat()
        )


        with open(
            self.state_path,
            "w",
            encoding="utf-8"
        ) as f:


            json.dump(
                self._state,
                f,
                ensure_ascii=False,
                indent=2
            )







    def _default(self):


        return {


            "version":"0.5",


            "last_updated":
                datetime.now().isoformat(),


            "last_decay":
                date.today().isoformat(),



            # 永久关系


            "bond_strength":
                0.10,


            "trust":
                0.30,


            "familiarity":
                0.20,


            "promise_level":
                0.0,


            "shared_history":
                0.0,



            # 近期状态


            "activity_level":
                0.20,



            # 关系事件


            "milestones":[],

            "important_events":[]


        }









    def _upgrade(
        self,
        data
    ):


        default=self._default()



        for k,v in default.items():

            if k not in data:

                data[k]=v



        data["version"]="0.5"


        return data







    # =========================
    # 时间衰减
    # =========================


    def _apply_daily_decay(self):


        today=date.today().isoformat()


        last=self._state.get(
            "last_decay",
            today
        )


        if today==last:

            return



        try:


            days=(

                date.fromisoformat(today)

                -

                date.fromisoformat(last)

            ).days


        except Exception:


            days=1





        if days<=0:

            return




        for _ in range(
            min(days,30)
        ):


            # 只衰减近期联系


            self._state["activity_level"]=max(

                0.05,

                self._state["activity_level"]*0.96

            )



        self._state["last_decay"]=today


        self._save()







    # =========================
    # 获取
    # =========================


    def get(self):


        return self._state




    def get_bond_strength(self):

        return self._state["bond_strength"]



    def get_trust(self):

        return self._state["trust"]



    def get_familiarity(self):

        return self._state["familiarity"]



    def get_promise_level(self):

        return self._state["promise_level"]



    def get_shared_history(self):

        return self._state["shared_history"]



    def get_activity(self):

        return self._state["activity_level"]







    # =========================
    # 更新关系
    # =========================


    def update_bond(
        self,
        delta
    ):


        self._state["bond_strength"]=min(

            1.0,

            self._state["bond_strength"]

            +

            max(0,delta)

        )


        self._save()





    def update_trust(
        self,
        delta
    ):


        self._state["trust"]=min(

            1.0,

            max(

                0,

                self._state["trust"]+delta

            )

        )


        self._save()






    def update_familiarity(
        self,
        delta
    ):


        self._state["familiarity"]=min(

            1.0,

            self._state["familiarity"]

            +

            max(0,delta)

        )


        self._save()






    def update_promise(
        self,
        delta
    ):


        self._state["promise_level"]=min(

            1.0,

            self._state["promise_level"]

            +

            max(0,delta)

        )


        self._save()






    def update_history(
        self,
        delta
    ):


        self._state["shared_history"]=min(

            1.0,

            self._state["shared_history"]

            +

            max(0,delta)

        )


        self._save()







    def update_activity(
        self,
        delta
    ):


        self._state["activity_level"]=min(

            1.0,

            max(

                0.05,

                self._state["activity_level"]+delta

            )

        )


        self._save()







    # =========================
    # 关系事件
    # =========================


    def add_milestone(
        self,
        event_id,
        topic
    ):


        self._state["milestones"].append({

            "event_id":event_id,

            "topic":topic,

            "time":
                datetime.now().isoformat()

        })


        self._save()






    def add_important_event(
        self,
        event
    ):


        self._state["important_events"].append(

            event

        )


        self._save()







    def get_milestones(self):

        return self._state.get(
            "milestones",
            []
        )








    # =========================
    # Prompt描述
    # =========================


    def to_prompt_text(self):


        parts=[]



        bond=self.get_bond_strength()

        trust=self.get_trust()

        promise=self.get_promise_level()




        if bond>0.7:

            parts.append(
                "拥有深厚羁绊"
            )

        elif bond>0.4:

            parts.append(
                "关系稳定"
            )

        else:

            parts.append(
                "正在建立连接"
            )





        if trust>0.7:

            parts.append(
                "高度信任清清"
            )

        elif trust>0.4:

            parts.append(
                "逐渐信任清清"
            )

        else:

            parts.append(
                "仍在认识阶段"
            )





        if promise>0.5:

            parts.append(
                "记得彼此的长期约定"
            )




        return (

            "与清清的关系："

            +

            "，".join(parts)

        )







    # =========================
    # 测试重置
    # =========================


    def reset(self):


        self._state=self._default()


        self._save()
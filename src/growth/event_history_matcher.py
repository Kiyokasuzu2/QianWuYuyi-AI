"""
事件历史匹配器（EventHistoryMatcher）

浅雾羽依成长系统 v0.6


职责:

判断:

这个事件是不是:

第一次发生

还是:

过去已经经历过


核心:

人生经历不能重复诞生


例如:

第一次告诉羽依名字

↓

形成身份


之后再次提到名字

↓

强化记忆


而不是重新创造身份


"""



from typing import List, Dict




class EventHistoryMatcher:



    def __init__(self):


        self.history=[]







    def build_key(
        self,
        event:Dict
    ):


        """
        人生事件唯一标识


        优先:

        event_identity

        其次:

        meaning + canonical_topic

        """


        identity=event.get(
            "event_identity"
        )



        if identity:


            return (

                "identity",

                identity

            )



        return (

            event.get(
                "category_id",
                ""
            ),


            event.get(
                "canonical_topic",
                event.get(
                    "topic",
                    ""
                )
            )

        )









    def already_exists(
        self,
        event
    ):



        key=self.build_key(
            event
        )



        for old in self.history:


            if old.get(
                "_history_key"
            )==key:


                return True



        return False









    def track(
        self,
        events:List[Dict],
        force_first_run=False
    ):



        result=[]



        for event in events:



            key=self.build_key(
                event
            )



            existed=False



            if not force_first_run:


                existed=self.already_exists(
                    event
                )





            event["_history_key"]=key



            if existed:


                event["is_first_occurrence"]=False


                event["memory_mode"]="reinforcement"



                print(

                    "🔁重复经历:",

                    event.get(
                        "canonical_topic"
                    )

                )



            else:


                event["is_first_occurrence"]=True


                event["memory_mode"]="formation"



                self.history.append(
                    event
                )


                print(

                    "🌱首次经历:",

                    event.get(
                        "canonical_topic"
                    )

                )




            result.append(
                event
            )



        return result









    def get_history(
        self
    ):


        return self.history







    def reset(
        self
    ):


        self.history=[]


        print(
            "🔄事件历史已重置"
        )
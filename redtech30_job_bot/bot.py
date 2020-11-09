from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount

from flask import Config

from botbuilder.ai.qna import QnAMaker, QnAMakerEndpoint
from botbuilder.ai.luis import LuisApplication, LuisRecognizer
from botbuilder.core import ActivityHandler, MessageFactory, TurnContext
from botbuilder.schema import ChannelAccount

from data_fetcher import JobDataFetcher
from utils.utils import IntentHandler

import logging
import numpy as np

class JobIntentHandler(IntentHandler):
    def __init__(self):
        super().__init__()
        self.data_fetcher = JobDataFetcher()

    def get_job(self):
        filter_options = self.get_entities()
        print ("Hello... ", filter_options)
        data = self.data_fetcher.get_job(**filter_options)
        if data.empty:
            return "No jobs found"
        else:
            print (data)
            # Job description,Technology,Years of experience,Where to apply,Location
            return_text = "We found a match \n\n"
            for index, row in data.iterrows():
                return_text += f"{row['Title']} \n {row['Job description']} at {row['Location']}"  
                if not row['Where to apply'] is np.nan:
                    return_text += "\n\n Find more details and apply here {row['Where to apply']} \n\n\n"
        return return_text

class JobBot(ActivityHandler):
    # See https://aka.ms/about-bot-activity-message to learn more about the message and other activity types.

    def __init__(self, config: Config):
     
        luis_application = LuisApplication(
            config.LUIS_APP_ID,
            config.LUIS_API_KEY,
            config.LUIS_API_HOST_NAME,
        )

        self._recognizer = LuisRecognizer(luis_application)

        self.qna_maker = QnAMaker(
            QnAMakerEndpoint(
                knowledge_base_id=config.QNA_KNOWLEDGEBASE_ID,
                endpoint_key=config.QNA_ENDPOINT_KEY,
                host=config.QNA_ENDPOINT_HOST,
            )
        )
        
    async def on_message_activity(self, turn_context: TurnContext):
        response = await self.qna_maker.get_answers(turn_context)
        if response and len(response) > 0:
            await turn_context.send_activity(MessageFactory.text(response[0].answer))
        else:
            intent_handler = JobIntentHandler()
            response = await self._recognizer.recognize(turn_context)
            return_text = intent_handler.handle(response)
            await turn_context.send_activity(return_text)

    async def on_members_added_activity(
        self,
        members_added: ChannelAccount,
        turn_context: TurnContext
    ):
        for member_added in members_added:
            if member_added.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hello and welcome to redtech30!")

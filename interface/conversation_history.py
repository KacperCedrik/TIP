import json
import os

class ConversationHistory:
    def __init__(self):
        with open("conversation_history.json", "r") as json_file:
            self.conversationContainer = json.load(json_file)

    def newConversation(self):
        conversation = dict.fromkeys(["id", "source", "target", "duration", "status", "messages-sent",
                                     "messages-sent-by-source", "messages-sent-by-target", ])
        return conversation

    def readConversationHistory(self):
        print(self.conversationContainer)

    def getConversationHistory(self):
        return self.conversationContainer

    def addConversation(self, conversation):
        conversationContainerLength = len(self.conversationContainer) + 1
        conversation["id"] = conversationContainerLength
        self.conversationContainer.append(conversation)

    def clearConversationHistory(self):
        self.conversationContainer = []

    def getJSON(self):
        temp = self.conversationContainer
        for conversation in temp:
            for key in conversation:
                if conversation[key] is None:
                    conversation[key] = "None"
        return json.dumps(temp)

    def printJSON(self):
        print(json.dumps(self.conversationContainer, indent=4))

    def saveConversationHistoryToFile(self):
        file = open("conversation_history.json", "w")
        file.truncate()
        file.write(self.getJSON())
        file.close()

    def readConversationHistoryFromFile(self):
        file = open("conversation_history.json", "r")
        content = file.read()
        file.close()
        return content

    def prettifyConversation(self, conversation):
        output = ""
        for key, value in conversation.items():
            output += str(key) + " - " + str(value) + "\n"
        return output

if __name__ == '__main__':
    convHis = ConversationHistory()
    conversation = {
        "source": "192.168.0.1",
        "target": "192.168.0.2",
        "duration": "00:23:47:09",
        "status": "ended-properly",
        "messages-sent": 13,
        "messages-sent-by-source": 7,
        "messages-sent-by-target": 6
    }
    conversationSub = {
        "source": "192.168.0.4",
        "target": "192.168.0.1",
        "duration": "00:13:47:09",
        "status": "ended-properly",
        "messages-sent": 13,
        "messages-sent-by-source": 7,
        "messages-sent-by-target": 6
    }
    convHis.readConversationHistory()
    convHis.addConversation(conversation)
    convHis.addConversation(conversationSub)
    convHis.readConversationHistory()
    convHis.printJSON()

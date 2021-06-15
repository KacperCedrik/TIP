import threading
import time
import functools
import conversation_history as ch


# decorator is a cool way of timing the ongoing task, however you can't read global variables in it

def timeit(func):
    @functools.wraps(func)
    def newfunc(*args, **kwargs):
        startTime = time.time()
        func(*args, **kwargs)
        elapsedTime = time.time() - startTime

        formatted_time = int(elapsedTime*1000)/1000

        print('function [{}] finished in {} s'.format(
            func.__name__, formatted_time))
    return newfunc


# global conversation history object
conversationHistoryController = ch.ConversationHistory()

def sample_conversation(x):
    startTime = time.time()
    conversation = conversationHistoryController.newConversation()
    for i in range(x):
        print(i)
    elapsedTime = time.time() - startTime
    formatted_time = int(elapsedTime * 1000) / 1000
    conversation["duration"] = formatted_time
    conversationHistoryController.addConversation(conversation)

def background_ongoing_task(time_to_sleep):
    while(True):
        time.sleep(time_to_sleep)
        conversationHistoryController.readConversationHistory()

if __name__ == "__main__":
    background_task = threading.Thread(target=background_ongoing_task, args=(3,))
    background_task.start()
    threadVar = threading.Thread(target=sample_conversation, args=(100000,))
    threadVar.start()
    threadVar_1 = threading.Thread(target=sample_conversation, args=(200000,))
    threadVar_1.start()
    threadVar_2 = threading.Thread(target=sample_conversation, args=(300000,))
    threadVar_2.start()



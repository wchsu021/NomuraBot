import logging
import telegram
import time
from flask import Flask, request
from script import Script
from econ import Econ
import configparser
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater,Dispatcher,CommandHandler,MessageHandler,Filters,ConversationHandler,CallbackContext, CallbackQueryHandler

# Enable logging
logging.basicConfig( format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO )
logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read("configure\\config.ini")
TOKEN = config['TELEGRAM']['TOKEN']

bot = telegram.Bot(token = TOKEN)

app = Flask(__name__)

@app.route('/hook', methods=['POST'])
def webhook_handler():
    """Set route /hook with POST method will trigger this method."""
    # print("request.method", request.method)
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), bot)

        # Update dispatcher process that handler to process this message
        dispatcher.process_update(update)
    return 'ok'

def start(update, _):
    
    '''
    æ­¡è¿ç«é¢
    '''
    user = update.message.from_user
    logger.info("User %s start the conversation.", user.first_name)
    
    text = "\nðä½ å¥½ï¼æ­¡è¿ä½¿ç¨éææä¿¡ççå°æ©å¨äººæåï¼\næåè´åæ¼æä¾çµ¦ä½¿ç¨èä¸åï¼æå¥æ¼çäººçè²¡å°å¡ï¼æ´çºé±ç§ãç¡å£åçé«é©ã\nå¨ä¿è­·æ¨åäººé±ç§çåæï¼æåè½å¤ ä¾ææ¨çç¶æ¿æ¦æ³ãç¶åçå¸å ´è¡æï¼ä»¥åè¿æçæ°èäºä»¶ï¼ä¾çºæ¨æ¨è¦æé©åä½ çåºéååã\n\nð©ç¾å¨å°±è¼¸å¥ /fund éå§èNomuraBotå°è«ï¼ççèªå·±çé¢¨éªçæ³å¦ä½å§ï¼\nðè¥è¦æ¥è©¢ä¸ä¸æ¬¡è©ä¼°çµæï¼å¯ä»¥è¼¸å¥ /result æ¥è©¢ï¼\n"
    update.message.reply_text('Hello, {}'.format(update.message.from_user.first_name)+text)

def start_script(update, _):
    
    '''
    éå§å°è©±åï¼è¥ä½¿ç¨èæå¡«éï¼ç¢ºèªæ¯å¦è¦éå¡«
    '''
    user = update.message.from_user
    logger.info("User %s start script.", user.first_name)

    global Script_handler
    Script_handler.reset_pointer(update.message.from_user.id)
    record = Script_handler.get_record(update.message.from_user.id)
    if record != None:
        reply_keyboard = [["æ¯","å¦"]]
        update.message.reply_text(
            'ä½ å·²ç¶åéé¢¨éªè©ä¼°åï¼æ¯å¦è¦éæ°è©ä¼°å¢?'
            ,reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        # bot.send_message(update.message.chat.id, 'ä½ å·²ç¶åéé¢¨éªè©ä¼°åï¼æ¯å¦è¦éæ°è©ä¼°å¢?', reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))

        return 99
        
    else:
        # bot.send_message(update.message.chat.id, 'éå§!\nè¥ä¸­éæ³é¢éé¢¨éªè©ä¼°æ¸¬è©¦ï¼è«è¼¸å¥ /cancel\n', reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardRemove())
        update.message.reply_text('æåéå§å§!\nè¥ä¸­éæ³é¢éé¢¨éªè©ä¼°æ¸¬è©¦ï¼è«è¼¸å¥ /cancel\n')
        # update.message.reply_text('è¥ä¸­éæ³é¢éé¢¨éªè©ä¼°æ¸¬è©¦ï¼è«è¼¸å¥ /cancel\n')

        now_id = Script_handler.get_pointer(update.message.from_user.id)
        ask_question(update, _)
        
        return now_id 

def cancel(update, _):
    
    '''
    è®ä½¿ç¨èä¸­éè·³åºå°è©±
    '''
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'ä½ å·²ç¶è·³åºé¢¨éªè©ä¼°\n'
        'å¦æä½ æ³è¦éæ°éå§æè³é¢¨éªè©ä¼°ï¼è«è¼¸å¥ /fund \n'
        , reply_markup=ReplyKeyboardRemove()
    )
    # bot.send_message(update.message.chat.id, 'ä½ å·²ç¶è·³åºé¢¨éªè©ä¼°\nå¦æä½ æ³è¦éæ°éå§æè³é¢¨éªè©ä¼°ï¼è«è¼¸å¥ /fund \n', reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardRemove())
    # global Script_handler
    # Script_handler.save_data()
    
    return ConversationHandler.END

def answer_format(update, _):

    '''
    æª¢æ¥åç­çæ ¼å¼æ¯å¦æ­£ç¢º
    '''
    global Script_handler
    user_id = update.message.from_user.id
    q_id = Script_handler.get_pointer(user_id)
    reply_text = update.message.text

    judge, _ = Script_handler.reply_preprocess(q_id, reply_text)
    return judge

def answer_recorder(update, _):
    
    '''
    è¥ä½¿ç¨èåç­çæ ¼å¼æ­£ç¢ºï¼åè¨éä¸ä¾
    ä¸¦æä¾æ©å¨äººçåé¥
    '''
    global Script_handler
    user_id = update.message.from_user.id
    q_id = Script_handler.get_pointer(user_id)
    reply_text = update.message.text

    judge, reply_revise = Script_handler.reply_preprocess(q_id, reply_text)

    Script_handler.save_answer(user_id, q_id, reply_revise)

    feedback_list = Script_handler.script_list.loc[q_id, "feedback"]
    feedback_list = eval(feedback_list)

    reply_idx = Script_handler.reply_process(q_id, reply_text)

    if len(feedback_list) > 1:
        if feedback_list[reply_idx] != None:
            feedback_text = feedback_list[reply_idx].split("/")
            update.message.reply_text(feedback_text[0], reply_markup=ReplyKeyboardRemove())
            # bot.send_message(update.message.chat.id, feedback_text[0], reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardRemove())
        
def get_next_question(update, _):
    
    '''
    è·³è½å°ä¸ä¸ååé¡
    '''
    global Script_handler
    user_id = update.message.from_user.id
    q_id = Script_handler.get_pointer(user_id)
    jump_list = Script_handler.script_list.loc[q_id, "jump"]
    jump_list = eval(jump_list)
    if len(jump_list) == 1:
        Script_handler.qa_id[str(user_id)] = jump_list[0]
        Script_handler.set_pointer(user_id, jump_list[0])
    else:
        answer_text = update.message.text
        answer_text = answer_text.upper()
        print("answer_text", answer_text)
        answer_id = ord(answer_text)
        answer_id -= 65
        Script_handler.set_pointer(user_id, jump_list[answer_id])
    
def ask_question(update, _):

    '''
    å¨telegramçé¢å°ä½¿ç¨èç¼å
    è¥çºé¸æ æä¾ä½¿ç¨èæé
    '''

    global Script_handler
    question = Script_handler.script_list.loc[Script_handler.qa_id[str(update.message.from_user.id)], "question"]
    q_type = Script_handler.script_list.loc[Script_handler.qa_id[str(update.message.from_user.id)], "type"]

    user = update.message.from_user
    logger.info("User %s ask question %s", user.first_name, str(Script_handler.script_list.loc[Script_handler.qa_id[str(update.message.from_user.id)], "id"]))
    
    if q_type == "å¡«å":
        update.message.reply_text(question, reply_markup=ReplyKeyboardRemove())
        # bot.send_message(update.message.chat.id, question, reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardRemove())
    elif q_type == "é¸æ":
        # reply_keyboard = [["A","B","C","D","E"]]
        choice = Script_handler.script_list.loc[Script_handler.qa_id[str(update.message.from_user.id)], "judgement"]
        choice = eval(choice)
        choice_list = []
        for i in range(len(choice)):
            choice_list.append(chr(i+65))
        reply_keyboard = []
        reply_keyboard.append(choice_list.copy())
        question_text = question
        for i in range(len(choice)):
            choice_str = chr(i+65)
            question_text = question_text + "\n" + choice_str + ":" + choice[i]

        update.message.reply_text(question_text, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),)
        # bot.send_message(update.message.chat.id, question_text, reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),)
    elif q_type == "è¤é¸":
        choice = Script_handler.script_list.loc[Script_handler.qa_id[str(update.message.from_user.id)], "judgement"]
        choice = eval(choice)
        choice_list = []
        for i in range(len(choice)):
            choice_list.append(chr(i+65))
        reply_keyboard = []
        reply_keyboard.append(choice_list.copy())
        question_text = question
        for i in range(len(choice)):
            choice_str = chr(i+65)
            question_text = question_text + "\n" + choice_str + ":" + choice[i]

        update.message.reply_text(question_text, reply_markup=ReplyKeyboardRemove())

def reply_handler(update, _):

    '''
    ä½¿ç¨èåè¦å¾çæ´å¥æµç¨
    1. æª¢æ¥æ ¼å¼
    2. è¥æ­£ç¢ºï¼å¾å°ç´éç­æ¡ åä¹ååç¥ä½¿ç¨è
    3. æåºåé¡(æ ¼å¼æ­£ç¢ºçºä¸ä¸é¡ æ ¼å¼é¯èª¤çºåé¡)
    '''

    # user = update.message.from_user
    # logger.info("User %s reply question", user.first_name)

    global Script_handler
    user = update.message.from_user
    logger.info("answer of %s: %s", user.first_name, update.message.text)

    format_judge = answer_format(update, _)
    
    if format_judge == True:
        answer_recorder(update, _)
        get_next_question(update, _)
    else:
        update.message.reply_text('æ ¼å¼é¯èª¤ï¼è«åå¡«ä¸æ¬¡\n', reply_markup=ReplyKeyboardRemove())
        # bot.send_message(update.message.chat.id, 'æ ¼å¼é¯èª¤ï¼è«åå¡«ä¸æ¬¡\n', reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardRemove())

    if Script_handler.qa_id[str(update.message.from_user.id)] != -1:
        now_id = Script_handler.get_pointer(update.message.from_user.id)
        ask_question(update, _)
        return now_id
    else:
        Script_handler.save_data()
        
        text = 'ä½ç­å®æ\n'
        text += 'âNomuraBotå·²çºä½ å®ææé©åçåºéï¼æ³ççèªå·±é©åæè³çåºéï¼è«è¼¸å¥ /result\n'
        text += 'ðè¥æ³åè©¦ä¸åçæè³æ¹æ³ï¼å¯ä»¥åæ¬¡è¼¸å¥ /fundï¼éæ°ç­é¡åï¼\n'

        update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())

        return ConversationHandler.END

def record_handler(update, _):

    '''
    è¥ä½¿ç¨èå·²æå¡«ç­ç´éï¼è©¢åæ¯å¦è¦éå
    '''
    global Script_handler
    
    user = update.message.from_user
    logger.info("check restart of %s: %s", user.first_name, update.message.text)

    if update.message.text == "æ¯":
        text = 'é£æåéæ°éå§å§!\n'
        text += 'è¥ä¸­éæ³é¢éé¢¨éªè©ä¼°æ¸¬è©¦ï¼è«è¼¸å¥ /cancel\n'
        update.message.reply_text(text)
        
        Script_handler.reset_pointer(update.message.from_user.id)
        now_id = Script_handler.get_pointer(update.message.from_user.id)
        ask_question(update, _)
        
        return now_id 
    else:
        update.message.reply_text('è¼¸å¥ /result ççæåçºä½ æ¨è¦çåºéå§\n', reply_markup=ReplyKeyboardRemove())
        # bot.send_message(update.message.chat.id, 'è¼¸å¥ /result ççæåçºä½ æ¨è¦çåºéå§\n', reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardRemove())
        return ConversationHandler.END

def fund_info_handler(update, _):

    '''
    æä¾æå®åºéçè©³ç´°è³æ
    '''

    user = update.message.from_user
    logger.info("User %s get short fund recommendation", user.first_name)
    
    if len(update.message.text) <= 6:
        update.message.reply_text('æ ¼å¼é¯èª¤', reply_markup=ReplyKeyboardRemove())
        # bot.send_message(update.message.chat.id, 'æ ¼å¼é¯èª¤', reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardRemove())
    else:
        global Econ_handler
        global Script_handler
        input_text = update.message.text[6:]
        fund_text = Econ_handler.get_fund_info(input_text)

        if fund_text == None:
            update.message.reply_text('æ±æ­ï¼æ¾ä¸å°æ¨æè¼¸å¥çåºé', reply_markup=ReplyKeyboardRemove())
            # bot.send_message(update.message.chat.id, 'æ±æ­ï¼æ¾ä¸å°æ¨æè¼¸å¥çåºé', reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardRemove())
        else:
            fund_item = "about_" + str(fund_text[-1])
            # update.message.reply_text(fund_text[0], reply_markup=ReplyKeyboardRemove())
            text = fund_text[0]
            text += "\n"
            # bot.send_message(update.message.chat.id, fund_text[0], reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardRemove())
            
            if Econ_handler.fund_pool.loc[fund_text[-1], "å°å"] in ["å¨ç", "èºç£", "ä¸­å"]:
                area_text = Econ_handler.fund_pool.loc[fund_text[-1], "å°å"] + "å¸å ´åæ"
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("é»æå°å®ç¶²", url = fund_text[-2])],
                    [InlineKeyboardButton(area_text, callback_data=fund_item)]
                ])
            else:
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("é»æå°å®ç¶²", url = fund_text[-2])]
                ])
            intro = Econ_handler.fund_pool.loc[fund_text[-1], "ç°¡ä»"]
            # bot.send_message(update.message.chat.id, intro, reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardRemove())
            # bot.send_message(update.message.chat.id, "æ¨åºéçè¿ä¸å¹´ç¸¾æçº: "+str(Econ_handler.fund_pool.loc[fund_text[-1], "ä¸å¹´ç¸¾æ"]), reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardRemove())
            intro = "ð¯"+intro
            text += intro
            text += "\n"
            period_list = Script_handler.get_period(update.message.chat.id)
            time_p = Script_handler.get_time(update.message.chat.id)
            
            if len(period_list) == 2 or len(period_list) == 1:
                profit = Econ_handler.cal_profit(Econ_handler.fund_pool.loc[fund_text[-1], "åç¨±"], time_p, period_list[0], None)
                # bot.send_message(update.message.chat.id, "ä¼°è¨çæé«èæä½å©æ½¤åå¥çº:"+str(profit[0])+" "+str(profit[1]), reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardRemove())
                annual_profit = Econ_handler.fund_pool.loc[fund_text[-1], "ä¸å¹´ç¸¾æ"]
                annual_profit = annual_profit*100
                annual_profit = round(annual_profit, 2)
                text = text + "ðæ¨åºéçè¿ä¸å¹´ç¸¾æçºï¼" + str(annual_profit) + "%\n"
                text = text + "ð¯æ¨è¨­å®çåºéæè³æé·çºï¼" + str(time_p) + "å¹´\n"
                text = text + "ð°æ¬åºéå¨æ­¤æè³æéçæå¤§æ¼²å¹ï¼" + str(profit[0]) + "%\n"
                text = text + "ð°æ¬åºéå¨æ­¤æè³æéçæå¤§è·å¹ï¼" + str(profit[1]) + "%\n"
                if len(period_list) == 1 or len(period_list) == 2:
                    
                    text = text + "ðæ¨é ä¼°æå¥çè³éçºï¼"
                    if len(period_list) == 1:
                        payoff = Econ_handler.cal_payoff(Econ_handler.fund_pool.loc[fund_text[-1], "åç¨±"], time_p, period_list[0], None)
                        text = text + str(period_list[0]*1000) + "å\n"
                    elif len(period_list) == 2:
                        payoff = Econ_handler.cal_payoff(Econ_handler.fund_pool.loc[fund_text[-1], "åç¨±"], time_p, period_list[0], period_list[1])
                        text = text + "åå§è³é " + str(period_list[0]*1000) +"åï¼æ¯ææå¥ "+str(period_list[1]*1000)+"å\n"
                    text = text + "ðçºæ¨é ä¼°çææ»¿æ¶ççºï¼" + str(payoff) +"å\n"
                    text = text + "(å°å®åï¼éåªæ¯å¤§è´çä¼°è¨ï¼ä¸¦éä¿è­çå ±é¬å)\n"

            else:
                # bot.send_message(update.message.chat.id, "æ±æ­ï¼ç®ä¸åºæé«èæä½å©æ½¤", reply_to_message_id = update.message.message_id, reply_markup = reply_markup)
                text += "ç®åç¡æ³å¾åºæ­¤åºéçæå¤§æ¼²è·å¹ï¼æ­¡è¿ä½ åå¾å®ç¶²æ¥è©¢è©³ç´°è³è¨å\n"
            
            update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
            update.message.reply_text("éæ³äºè§£ä»éº¼ï¼", reply_markup=reply_markup)
            # bot.send_message(update.message.chat.id, "éæ³äºè§£ä»éº¼ï¼", reply_to_message_id = update.message.message_id, reply_markup = reply_markup)

def more_info(update, _):
    
    '''
    æä¾å°åçç¸½ç¶åæå
    '''

    # user = update.message.from_user
    # logger.info("User %s get area analysis", user.first_name)

    global Econ_handler
    if update.callback_query.data[:5] == "about":
        # bot.send_chat_action(chat_id = update.callback_query.message.chat_id, action = telegram.ChatAction.TYPING)
        # time.sleep(1)
        area = Econ_handler.fund_pool.loc[int(update.callback_query.data[6:]), "å°å"]
        update.callback_query.edit_message_text("ä»¥ä¸æ¯ " + Econ_handler.fund_pool.loc[int(update.callback_query.data[6:]), "å°å"] + " çç¸½é«ç¶æ¿åæï¼")
        PATH = 'database/market_graph/'
        if area == "èºç£":
            bot.send_photo(chat_id = update.callback_query.message.chat_id, photo=open(PATH+area+'.PNG', 'rb'))
        elif area == "ä¸­å":
            bot.send_photo(chat_id = update.callback_query.message.chat_id, photo=open(PATH+area+'.PNG', 'rb'))
        elif area == "å¨ç":
            bot.send_photo(chat_id = update.callback_query.message.chat_id, photo=open(PATH+area+'.PNG', 'rb'))
        else:
            pass

    else:
        update.callback_query.edit_message_text("æ±æ­ï¼æåç®åç¡æ³è©²å°åçç¸½ç¶åæåï¼ä½ å¯ä»¥å°å®ç¶²æ¥è©¢è©³ç´°çå¸å ´åæ")

def more_fund_list(update, _):

    '''
    æä¾ä½¿ç¨èå®æ´çåºéæ¸å®
    '''

    user = update.message.from_user
    logger.info("User %s get long fund recommendation", user.first_name)
    
    global Script_handler
    global Econ_handler
    risk_result = Script_handler.risk_judge(update.message.from_user.id)
    # recommend_fund = Econ_handler.fund_evaluation()
    recommend_list = Econ_handler.fund_filter(risk_result)
    recommend_list = Econ_handler.get_short_recommend_list(recommend_list)
    
    fund_text = Econ_handler.gen_recommend_text(recommend_list, risk_result, False)
    update.message.reply_text(fund_text, reply_markup=ReplyKeyboardRemove())

def result(update, _):

    """
    æä¾ä½¿ç¨èé¢¨éªææ¨è©ä¼°ççµæï¼ä¸¦æä¾ç­ççåºéæ¨è¦æ¸å®
    """

    user = update.message.from_user
    logger.info("User %s get result", user.first_name)

    update.message.reply_text('æ­£å¨å¹«ä½ è©ä¼°é©åçåºé...', reply_markup=ReplyKeyboardRemove())
    
    global Script_handler
    global Econ_handler
    answer_record = Script_handler.get_record(update.message.from_user.id)
    if answer_record != None:
        
        risk_result = Script_handler.risk_judge(update.message.from_user.id)
        recommend_fund = Econ_handler.fund_evaluation()
        recommend_list = Econ_handler.fund_filter(risk_result)
        recommend_list = Econ_handler.get_short_recommend_list(recommend_list)
        fund_text = Econ_handler.gen_recommend_text(recommend_list, risk_result, True)
        reply_list = [
            "ä½ æ¯åå¸ææç©©å®å ±é¬ä¸è¼ä¸é¡ææ¥åæå¤±ï¼å±¬æ¼ä¿å®åçæè³äººå¦ï¼",
            "ä½ æ¯åå¸ææç©©å®å ±é¬ä¸è¼ä¸é¡ææ¥åæå¤±ï¼å±¬æ¼ä¿å®åçæè³äººå¦ï¼",
            "ä½ æ¯åå¸æè³ç¢ç©©å®æé·ä¸è½æ¿åå°æ³¢åé¢¨éªï¼å±¬æ¼ç©©å¥åçæè³äººå¦ï¼",
            "ä½ æ¯åå¸æè¿½æ±æå¤§çè³æ¬å©å¾ä¸è½æ¿åè¼å¤§è³ç¢æ³¢åï¼å±¬æ¼ç©æ¥µæé·åçæè³äººå¦ï¼",
            "ä½ æ¯åå¸æè¿½æ±æå¤§çè³æ¬å©å¾ä¸è½æ¿åè¼å¤§è³ç¢æ³¢åï¼å±¬æ¼ç©æ¥µæé·åçæè³äººå¦ï¼"
        ]
        update.message.reply_text("ð©NomuraBotç¶éè¨ç®åè©ä¼°å¾ï¼èªçºä½ çé¢¨éªå¯æ¿åç¨åº¦çºï¼ RR"+str(risk_result)+"\n"+reply_list[risk_result-1], reply_markup=ReplyKeyboardRemove())
        update.message.reply_text(fund_text, reply_markup=ReplyKeyboardRemove())
        
        text = "ðï¸ä½ å¯ä»¥è¼¸å¥ /more æ¥çå®æ´çåºéæ¨è¦æ¸å®å\n"
        text += "ðä½ å¯ä»¥è¼¸å¥ /info +ä½ æ³è¦æ¥è©¢çåºéåç¨±ä¾ççè©²åºéçè©³ç´°è³è¨\n(âå°å®åï¼ä¸­éè¦ç©ºä¸æ ¼åï¼ä¾å¦: /info éæåªè³ªåºé)"
        update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
    else:
        update.message.reply_text("ä½ å°æªå®æé¢¨éªè©ä¼°éè¡¨ï¼è«è¼¸å¥ /fund å®æé¢¨éªè©ä¼°", reply_markup=ReplyKeyboardRemove())

def error_handler(update, context: CallbackContext):
    
    '''
    é¯èª¤è¨æ¯èç
    '''
    bot.send_chat_action(chat_id = update.message.chat_id, action = telegram.ChatAction.TYPING)
    time.sleep(1)
    update.message.reply_text("æ±æ­ï¼ç®åNomuraBotåºäºé»å°åé¡ï¼è«ç¨ç­ä¸ä¸")

def error(update, context):
    
    """
    è¨éUpdatesæåºç¾çerrorsãåºç¾erroræconsoleå°±æprintåºä¸é¢logger.warningçå§å®¹
    """
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    
    """
    ç³»çµ±éä½æµç¨
    å¨FLASKæ¶æ§ä¸ç¨ä¸å°æ­¤æ­¥é©
    """
    global Script_handler
    state_dict = {}
    for i in range(len(Script_handler.script_list)):
        state_dict[i] = [MessageHandler(Filters.text & ~Filters.command, reply_handler)]

    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('fund', start_script)],

        states=state_dict,
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("result", result))
    dispatcher.add_handler(conv_handler)
    dispatcher.add_error_handler(error_handler)
    dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

Script_handler = Script()
Econ_handler = Econ()
state_dict = {}
for i in range(len(Script_handler.script_list)):
    state_dict[i] = [MessageHandler(Filters.text & ~Filters.command, reply_handler)]

state_dict[99] = [MessageHandler(Filters.text & ~Filters.command, record_handler)]

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('fund', start_script)],
    states=state_dict,
    fallbacks=[CommandHandler('cancel', cancel)],
)

# updater = Updater(TOKEN)
# dispatcher = updater.dispatcher
dispatcher = Dispatcher(bot, None)

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("result", result))
dispatcher.add_handler(conv_handler)
dispatcher.add_handler(CommandHandler("info", fund_info_handler))
dispatcher.add_handler(CommandHandler("more", more_fund_list))
dispatcher.add_handler(CallbackQueryHandler(more_info))
dispatcher.add_error_handler(error_handler)
dispatcher.add_error_handler(error)

# updater.start_polling()
# updater.idle()

if __name__ == '__main__':
    
    # main()
    app.run(debug=True)
    # app.run(host='0.0.0.0', port=5000, debug = True)

    #https://b5d32bb758fe.ngrok.io
    #https://api.telegram.org/bot1753648492:AAHJA7mz8UCTVicoizQbV8D5MNdSpIImfWE/setWebhook?url=https://b5d32bb758fe.ngrok.io/hook
    
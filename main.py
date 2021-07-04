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
    歡迎畫面
    '''
    user = update.message.from_user
    logger.info("User %s start the conversation.", user.first_name)
    
    text = "\n📍你好，歡迎使用野村投信的理專機器人服務！\n我們致力於提供給使用者一個，有別於真人理財專員，更為隱私、無壓力的體驗。\n在保護您個人隱私的同時，我們能夠依據您的經濟概況、當前的市場行情，以及近期的新聞事件，來為您推薦最適合你的基金商品。\n\n🚩現在就輸入 /fund 開始與NomuraBot對談，看看自己的風險狀況如何吧！\n📁若要查詢上一次評估結果，可以輸入 /result 查詢！\n"
    update.message.reply_text('Hello, {}'.format(update.message.from_user.first_name)+text)

def start_script(update, _):
    
    '''
    開始對話前，若使用者有填過，確認是否要重填
    '''
    user = update.message.from_user
    logger.info("User %s start script.", user.first_name)

    global Script_handler
    Script_handler.reset_pointer(update.message.from_user.id)
    record = Script_handler.get_record(update.message.from_user.id)
    if record != None:
        reply_keyboard = [["是","否"]]
        update.message.reply_text(
            '你已經做過風險評估囉！是否要重新評估呢?'
            ,reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        # bot.send_message(update.message.chat.id, '你已經做過風險評估囉！是否要重新評估呢?', reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True))

        return 99
        
    else:
        # bot.send_message(update.message.chat.id, '開始!\n若中途想離開風險評估測試，請輸入 /cancel\n', reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardRemove())
        update.message.reply_text('我們開始吧!\n若中途想離開風險評估測試，請輸入 /cancel\n')
        # update.message.reply_text('若中途想離開風險評估測試，請輸入 /cancel\n')

        now_id = Script_handler.get_pointer(update.message.from_user.id)
        ask_question(update, _)
        
        return now_id 

def cancel(update, _):
    
    '''
    讓使用者中途跳出對話
    '''
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        '你已經跳出風險評估\n'
        '如果你想要重新開始投資風險評估，請輸入 /fund \n'
        , reply_markup=ReplyKeyboardRemove()
    )
    # bot.send_message(update.message.chat.id, '你已經跳出風險評估\n如果你想要重新開始投資風險評估，請輸入 /fund \n', reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardRemove())
    # global Script_handler
    # Script_handler.save_data()
    
    return ConversationHandler.END

def answer_format(update, _):

    '''
    檢查回答的格式是否正確
    '''
    global Script_handler
    user_id = update.message.from_user.id
    q_id = Script_handler.get_pointer(user_id)
    reply_text = update.message.text

    judge, _ = Script_handler.reply_preprocess(q_id, reply_text)
    return judge

def answer_recorder(update, _):
    
    '''
    若使用者回答的格式正確，則記錄下來
    並提供機器人的回饋
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
    跳轉到下一個問題
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
    在telegram界面對使用者發問
    若為選擇 提供使用者按鈕
    '''

    global Script_handler
    question = Script_handler.script_list.loc[Script_handler.qa_id[str(update.message.from_user.id)], "question"]
    q_type = Script_handler.script_list.loc[Script_handler.qa_id[str(update.message.from_user.id)], "type"]

    user = update.message.from_user
    logger.info("User %s ask question %s", user.first_name, str(Script_handler.script_list.loc[Script_handler.qa_id[str(update.message.from_user.id)], "id"]))
    
    if q_type == "填充":
        update.message.reply_text(question, reply_markup=ReplyKeyboardRemove())
        # bot.send_message(update.message.chat.id, question, reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardRemove())
    elif q_type == "選擇":
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
    elif q_type == "複選":
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
    使用者回覆後的整套流程
    1. 檢查格式
    2. 若正確，後台紀錄答案 反之則告知使用者
    3. 提出問題(格式正確為下一題 格式錯誤為原題)
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
        update.message.reply_text('格式錯誤，請再填一次\n', reply_markup=ReplyKeyboardRemove())
        # bot.send_message(update.message.chat.id, '格式錯誤，請再填一次\n', reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardRemove())

    if Script_handler.qa_id[str(update.message.from_user.id)] != -1:
        now_id = Script_handler.get_pointer(update.message.from_user.id)
        ask_question(update, _)
        return now_id
    else:
        Script_handler.save_data()
        
        text = '作答完成\n'
        text += '✅NomuraBot已為你安排最適合的基金，想看看自己適合投資的基金，請輸入 /result\n'
        text += '🔄若想嘗試不同的投資方法，可以再次輸入 /fund，重新答題喔！\n'

        update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())

        return ConversationHandler.END

def record_handler(update, _):

    '''
    若使用者已有填答紀錄，詢問是否要重做
    '''
    global Script_handler
    
    user = update.message.from_user
    logger.info("check restart of %s: %s", user.first_name, update.message.text)

    if update.message.text == "是":
        text = '那我們重新開始吧!\n'
        text += '若中途想離開風險評估測試，請輸入 /cancel\n'
        update.message.reply_text(text)
        
        Script_handler.reset_pointer(update.message.from_user.id)
        now_id = Script_handler.get_pointer(update.message.from_user.id)
        ask_question(update, _)
        
        return now_id 
    else:
        update.message.reply_text('輸入 /result 看看我們為你推薦的基金吧\n', reply_markup=ReplyKeyboardRemove())
        # bot.send_message(update.message.chat.id, '輸入 /result 看看我們為你推薦的基金吧\n', reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardRemove())
        return ConversationHandler.END

def fund_info_handler(update, _):

    '''
    提供指定基金的詳細資料
    '''

    user = update.message.from_user
    logger.info("User %s get short fund recommendation", user.first_name)
    
    if len(update.message.text) <= 6:
        update.message.reply_text('格式錯誤', reply_markup=ReplyKeyboardRemove())
        # bot.send_message(update.message.chat.id, '格式錯誤', reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardRemove())
    else:
        global Econ_handler
        global Script_handler
        input_text = update.message.text[6:]
        fund_text = Econ_handler.get_fund_info(input_text)

        if fund_text == None:
            update.message.reply_text('抱歉，找不到您所輸入的基金', reply_markup=ReplyKeyboardRemove())
            # bot.send_message(update.message.chat.id, '抱歉，找不到您所輸入的基金', reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardRemove())
        else:
            fund_item = "about_" + str(fund_text[-1])
            # update.message.reply_text(fund_text[0], reply_markup=ReplyKeyboardRemove())
            text = fund_text[0]
            text += "\n"
            # bot.send_message(update.message.chat.id, fund_text[0], reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardRemove())
            
            if Econ_handler.fund_pool.loc[fund_text[-1], "地區"] in ["全球", "臺灣", "中國"]:
                area_text = Econ_handler.fund_pool.loc[fund_text[-1], "地區"] + "市場分析"
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("點我到官網", url = fund_text[-2])],
                    [InlineKeyboardButton(area_text, callback_data=fund_item)]
                ])
            else:
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("點我到官網", url = fund_text[-2])]
                ])
            intro = Econ_handler.fund_pool.loc[fund_text[-1], "簡介"]
            # bot.send_message(update.message.chat.id, intro, reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardRemove())
            # bot.send_message(update.message.chat.id, "您基金的近一年績效為: "+str(Econ_handler.fund_pool.loc[fund_text[-1], "一年績效"]), reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardRemove())
            intro = "🎯"+intro
            text += intro
            text += "\n"
            period_list = Script_handler.get_period(update.message.chat.id)
            time_p = Script_handler.get_time(update.message.chat.id)
            
            if len(period_list) == 2 or len(period_list) == 1:
                profit = Econ_handler.cal_profit(Econ_handler.fund_pool.loc[fund_text[-1], "名稱"], time_p, period_list[0], None)
                # bot.send_message(update.message.chat.id, "估計的最高與最低利潤分別為:"+str(profit[0])+" "+str(profit[1]), reply_to_message_id = update.message.message_id, reply_markup = ReplyKeyboardRemove())
                annual_profit = Econ_handler.fund_pool.loc[fund_text[-1], "一年績效"]
                annual_profit = annual_profit*100
                annual_profit = round(annual_profit, 2)
                text = text + "📈您基金的近一年績效為：" + str(annual_profit) + "%\n"
                text = text + "🎯您設定的基金投資期長為：" + str(time_p) + "年\n"
                text = text + "💰本基金在此投資期間的最大漲幅：" + str(profit[0]) + "%\n"
                text = text + "💰本基金在此投資期間的最大跌幅：" + str(profit[1]) + "%\n"
                if len(period_list) == 1 or len(period_list) == 2:
                    
                    text = text + "🏆您預估投入的資金為："
                    if len(period_list) == 1:
                        payoff = Econ_handler.cal_payoff(Econ_handler.fund_pool.loc[fund_text[-1], "名稱"], time_p, period_list[0], None)
                        text = text + str(period_list[0]*1000) + "元\n"
                    elif len(period_list) == 2:
                        payoff = Econ_handler.cal_payoff(Econ_handler.fund_pool.loc[fund_text[-1], "名稱"], time_p, period_list[0], period_list[1])
                        text = text + "初始資金 " + str(period_list[0]*1000) +"元，每月投入 "+str(period_list[1]*1000)+"元\n"
                    text = text + "📈為您預估的期滿收益為：" + str(payoff) +"元\n"
                    text = text + "(小叮嚀：這只是大致的估計，並非保證的報酬喔)\n"

            else:
                # bot.send_message(update.message.chat.id, "抱歉，算不出最高與最低利潤", reply_to_message_id = update.message.message_id, reply_markup = reply_markup)
                text += "目前無法得出此基金的最大漲跌幅，歡迎你前往官網查詢詳細資訊喔\n"
            
            update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
            update.message.reply_text("還想了解什麼？", reply_markup=reply_markup)
            # bot.send_message(update.message.chat.id, "還想了解什麼？", reply_to_message_id = update.message.message_id, reply_markup = reply_markup)

def more_info(update, _):
    
    '''
    提供地區的總經分析圖
    '''

    # user = update.message.from_user
    # logger.info("User %s get area analysis", user.first_name)

    global Econ_handler
    if update.callback_query.data[:5] == "about":
        # bot.send_chat_action(chat_id = update.callback_query.message.chat_id, action = telegram.ChatAction.TYPING)
        # time.sleep(1)
        area = Econ_handler.fund_pool.loc[int(update.callback_query.data[6:]), "地區"]
        update.callback_query.edit_message_text("以下是 " + Econ_handler.fund_pool.loc[int(update.callback_query.data[6:]), "地區"] + " 的總體經濟分析：")
        PATH = 'database/market_graph/'
        if area == "臺灣":
            bot.send_photo(chat_id = update.callback_query.message.chat_id, photo=open(PATH+area+'.PNG', 'rb'))
        elif area == "中國":
            bot.send_photo(chat_id = update.callback_query.message.chat_id, photo=open(PATH+area+'.PNG', 'rb'))
        elif area == "全球":
            bot.send_photo(chat_id = update.callback_query.message.chat_id, photo=open(PATH+area+'.PNG', 'rb'))
        else:
            pass

    else:
        update.callback_query.edit_message_text("抱歉，我們目前無法該地區的總經分析圖，你可以到官網查詢詳細的市場分析")

def more_fund_list(update, _):

    '''
    提供使用者完整的基金清單
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
    提供使用者風險指標評估的結果，並提供短版的基金推薦清單
    """

    user = update.message.from_user
    logger.info("User %s get result", user.first_name)

    update.message.reply_text('正在幫你評估適合的基金...', reply_markup=ReplyKeyboardRemove())
    
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
            "你是個希望有穩定報酬且較不願意接受損失，屬於保守型的投資人哦！",
            "你是個希望有穩定報酬且較不願意接受損失，屬於保守型的投資人哦！",
            "你是個希望資產穩定成長且能承受小波動風險，屬於穩健型的投資人哦！",
            "你是個希望追求最大的資本利得且能承受較大資產波動，屬於積極成長型的投資人哦！",
            "你是個希望追求最大的資本利得且能承受較大資產波動，屬於積極成長型的投資人哦！"
        ]
        update.message.reply_text("🚩NomuraBot經過計算和評估後，認為你的風險可承受程度為： RR"+str(risk_result)+"\n"+reply_list[risk_result-1], reply_markup=ReplyKeyboardRemove())
        update.message.reply_text(fund_text, reply_markup=ReplyKeyboardRemove())
        
        text = "🗒️你可以輸入 /more 查看完整的基金推薦清單喔\n"
        text += "📊你可以輸入 /info +你想要查詢的基金名稱來看看該基金的詳細資訊\n(❗小叮嚀：中間要空一格喔，例如: /info 野村優質基金)"
        update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
    else:
        update.message.reply_text("你尚未完成風險評估量表，請輸入 /fund 完成風險評估", reply_markup=ReplyKeyboardRemove())

def error_handler(update, context: CallbackContext):
    
    '''
    錯誤訊息處理
    '''
    bot.send_chat_action(chat_id = update.message.chat_id, action = telegram.ChatAction.TYPING)
    time.sleep(1)
    update.message.reply_text("抱歉，目前NomuraBot出了點小問題，請稍等一下")

def error(update, context):
    
    """
    記錄Updates時出現的errors。出現error時console就會print出下面logger.warning的內容
    """
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    
    """
    系統運作流程
    在FLASK架構下用不到此步驟
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
    
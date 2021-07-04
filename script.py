import pandas as pd
import numpy as np
import csv

class Script():

	def __init__(self):

		self.answer_record = []   ## 記錄每位使用者的回答

		self.script_list = self.load_script()   ## 腳本的問題與選項

		self.qa_id = {}   ## 記錄每個使用者目前正在第幾題

		self.load_record()  ## 匯入之前存起來的使用者回答

	def load_record(self):

		## 讀入使用者回答記錄
		## 如果找不到檔案，就不匯入
		try:
			dataframe = pd.read_csv('database/data.csv')
			# dataframe = pd.read_csv('database/data.csv', encoding='utf-8')
			self.answer_record = dataframe.to_dict('records')
			print("Load successfully!")
		except:
			print("No previous data!")
	
	def load_script(self):

		## 讀入劇本
		qa_list = pd.read_csv('database/qa_list.csv')
		return qa_list

	def get_pointer(self, user_id):

		## 回傳指定使用者目前在第幾題
		return self.qa_id[str(user_id)]

	def set_pointer(self, user_id, q_id):

		## 當使用者進到下一題時，更改題號記錄
		self.qa_id[str(user_id)] = q_id

	def save_answer(self, user_id, q_id, answer):

		## 記錄使用者某一題的答案
		exist = False	## 使用者是否已經回答過

		## 找尋使用者的回答記錄，若有，則直接更改該題的答案
		for d in self.answer_record:
			if d["user_id"] == user_id:
				d[str(q_id)] = answer
				exist = True
				break
		
		## 使用者沒有回答過的話，需要建立一個新位子來儲存該使用者的ID及答題資訊
		if exist == False:
			new_d = {}
			new_d["user_id"] = user_id
			for i in range(len(self.script_list)):
				new_d[str(i)] = None
			new_d[str(q_id)] = answer
			self.answer_record.append(new_d)

		print("Save answer!", answer)
		pass

	def get_record(self, user_id):
		
		## 抓取某個使用者的所有回答
		for d in self.answer_record:
			if d["user_id"] == user_id:
				return d
		return None

	def get_period(self, user_id):

		## 抓取指定使用者的投資金額
		## 若為單筆投入，抓取投入金額
		## 若為每月投入，抓取初始金額與每月投入金額
		period_list = []
		for d in self.answer_record:
			if d["user_id"] == user_id:
				if d['2'] == 'A':
					period_list.append(d['3'])
				elif d['2'] == 'B':
					period_list.append(d['4'])
					period_list.append(d['5'])
				return period_list
		return []

	def get_time(self, user_id):

		## 抓取指定使用者的投資期長
		for d in self.answer_record:
			if d["user_id"] == user_id:
				return d['8']
		return None

	def save_data(self):

		## 將使用者的回答輸出至csv檔
		key = self.answer_record[0].keys()
		print("!!!!!!!!!!!! Start output to csv !!!!!!!!!!")
		# print(self.answer_record)
		with open('database/data.csv', 'w', newline='', encoding='utf-8')  as output_file:
			dict_writer = csv.DictWriter(output_file, key)
			dict_writer.writeheader()
			dict_writer.writerows(self.answer_record)
		print("!!!!!!!!!!!! Finish output to csv !!!!!!!!!!")

	def print_answer(self, user_id):
		
		## 把答案印出來
		print("PRINT")
		check = False
		for d in self.answer_record:
			if d["user_id"] == str(user_id):
				check = True
				print(d)
				break

		if check == False:
			print("No user: "+ str(user_id))

	def risk_judge(self, user_id):

		## 計算風險指標
		record = self.get_record(user_id)
		print("record", record)
		judge_list = []
		for i in range(len(record.keys())-1):
			q_type = self.script_list.loc[i, "type"]
			reply = record[str(i)]
			q_weight = self.script_list.loc[i, "weight"]
			if q_type == "選擇":
				pts = self.script_list.loc[i, "points"]
				pts = eval(pts)
				reply_idx = ord(reply)-65
				if q_weight > 0:
					judge_list.append(pts[reply_idx])

			elif q_type == "填充":
				
				if q_weight > 0:
					pts = self.script_list.loc[i, "points"]
					pts = eval(pts)
					criteria = self.script_list.loc[i, "judgement"]
					criteria = eval(criteria)
					reply_num = int(reply)
					reply_idx = len(criteria)
					for c in range(len(criteria)):
						if reply_num >= criteria[c]:
							reply_idx = c
							break
					judge_list.append(pts[reply_idx])
			
			elif q_type == "複選":
				pts = self.script_list.loc[i, "points"]
				pts = eval(pts)
				reply_idx = ord(reply)-65
				if q_weight > 0:
					judge_list.append(pts[reply_idx])
		
		score = judge_list.copy()
		risk_level = 0
		if np.mean(score) < 1.5:
			risk_level = 1
		elif np.mean(score) >= 1.5 and np.mean(score) < 2:
			risk_level = 2
		elif np.mean(score) >= 2 and np.mean(score) < 3:
			risk_level = 3
		elif np.mean(score) >= 3 and np.mean(score) < 4:
			risk_level = 4
		elif np.mean(score) >= 4:
			risk_level = 5
		
		print("score: ", score, risk_level)
		return risk_level

	def reset_pointer(self, user_id):

		## 將某個使用者的問題指標重設
		if str(user_id) not in self.qa_id.keys():
			self.qa_id[str(user_id)] = 0
		else:
			self.qa_id[str(user_id)] = 0

	def reply_process(self, q_id, reply):

		## 將使用者的回答量化成1~5
		i = q_id
		reply_idx = None
		q_type = self.script_list.loc[i, "type"]
		reply = reply.upper()
		# reply = record[str(i)]
		q_weight = self.script_list.loc[i, "weight"]
		if q_type == "選擇":
			pts = self.script_list.loc[i, "points"]
			pts = eval(pts)
			reply_idx = ord(reply)-65

		elif q_type == "填充":
			
			if q_weight > 0:
				pts = self.script_list.loc[i, "points"]
				pts = eval(pts)
				criteria = self.script_list.loc[i, "judgement"]
				criteria = eval(criteria)
				reply_num = int(reply)
				reply_idx = len(criteria)
				for c in range(len(criteria)):
					if reply_num >= criteria[c]:
						reply_idx = c
						break

		elif q_type == "複選":

			reply_idx = ord(reply[-1])-65

		
		return reply_idx

	def reply_preprocess(self, q_id, reply_text):

		## 檢查使用者的回答是否符合格式條件
		if q_id in [0,1,2,6,10,11,12,13]:
			format_list = "AaBbCcDdEeFf"
			choice = self.script_list.loc[q_id, "judgement"]
			choice = eval(choice)
			# print("reply", reply_text)
			# print(len(reply_text))
			# print(format_list[:len(choice)*2])
			
			if len(reply_text) == 1 and reply_text[0] in format_list[:len(choice)*2]:
				return True, reply_text.upper()
			else:
				return False, None
		elif q_id in [3,4,5]:
			try:
				money = int(reply_text)
				if money > 0:
					return True, money
				else:
					return False, None
			except:
				return False, None
		elif q_id in [8]:
			try:
				money = int(reply_text)
				if money > 0 and money <= 10:
					return True, money
				else:
					return False, None
			except:
				return False, None
		elif q_id in [9]:
			try:
				format_list = "AaBbCcDdEeFf"
				if len(reply_text) < 1 or len(reply_text) > 6:
					return False, None
				for w in reply_text:
					if w not in format_list:
						return False, None
				reply_text = reply_text.upper()
				if "A" in reply_text and len(reply_text) > 1:
					return False, None
				for x in reply_text:
					if reply_text.count(x) > 1:
						return False, None
				return True, reply_text[-1]
			except:
				return False, None
		else:
			return True, reply_text
		
if __name__ == '__main__':

	test_script = Script()
	
	## 測試問題與選項
	# print(test_script.script_list)
	# print(test_script.script_list.columns)
	# question = test_script.script_list.loc[test_script.qa_id, "question"]
	# print(question)
	# choice = test_script.script_list.loc[test_script.qa_id, "judgement"]
	# print(choice)
	
	## 測試風險指標的計算
	# test_script = Script()
	# test_script.load_record()
	# print(test_script.answer_record)
	# user_id = test_script.answer_record[0]['user_id']
	# test_script.risk_judge(user_id)

	pass

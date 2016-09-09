import string
import re
import time
import redis
import MySQLdb
import requests

w = list()
conn = MySQLdb.connect(host='localhost',port=8999,user='wei',passwd='hehe',db='github')
keyword = ["qufenqi","laifenqi","qudian"]
whitelist = []
user_agent = "User-Agent: Mozilla/5.0 (Windows NT 6.3; WOW64; rv:35.0) Gecko/20100101 Firefox/35.0 security_test"

class githubscan:
	def __init__(self,key):
		self.key = key

	def find_count(self,s):
		m = re.search(r'">(\d+?)</a> <a class="next_page" rel="next"',s)
		if m:
			count = int(m.group(1))
			print "count = " + m.group(1)
		else:
			count = 0
			print "no count!!!"
		return count

	def find_time(self,s):
		m = re.findall(r'Last indexed <relative-time datetime="(\S{20})">',s)
		if m:
			time = list()
			for t in m:
				time.append(t)
		else:
			print "no time!!!"
		return time

	def find_url(self,s):
		m = re.findall(r'&#8211;\n      <a href="(\S+?)" title',s)
		if m:
			url = list()
			for r in m:
				r = "https://github.com"+r
				url.append(r)
		else:
			print "no url!!!"
		return url

	def find_username(self,s):
		m = re.findall(r'"><img alt="@(.+?)" class',s)
		if m:
			username = list()
			for r in m:
				username.append(r)
		else:
			print "no username!!!"
		return username

	def find_reponame(self,s):
		m = re.findall(r'">(.+?)</a> <br>\n      <span class="text-small text-gray match-count">',s)
		if m:
			print m
			reponame = list()
			for r in m:
				reponame.append(r)
		else:
			print "no reponame!!!"
		return reponame
			
	def run(self):
		the_url = list()
		the_time = list()
		the_username = list()
		the_reponame = list()
		tur  = list()
		result = dict()
		session = requests.Session()
		url1 = "https://github.com/login"
		rep1 = session.get(url1)
		pattern = re.compile(r'<input name="authenticity_token" type="hidden" value="(.*)" />')
		a_token = pattern.findall(rep1.content)[0]

		url2 = "https://github.com/session"
		data2 = {
			'commit':'Sign+in',
			'utf8':'%E2%9C%93',
			'authenticity_token':a_token,
			'login':'mrwei0323',
			'password':'12qw!@QW'
		}
		rep2 = session.post(url2,data=data2)

		url3 = "https://github.com/search?&q="+self.key+"&type=Code"
		rep3 = session.get(url3)
		print "get total page num..."
		page_num = self.find_count(rep3.content)
		print "get total num done!!!"
		print "send each request..."
		t = 0
		for i in range(1,page_num+1):
			target = 'https://github.com/search?p='+str(i)+'&q="'+self.key+'"&ref=searchresults&type=Code'
			print target
			time.sleep(5)
			thehtml = session.get(target)
			html = thehtml.content
			if html is not None:
				print html
				the_url = self.find_url(html)
				the_time = self.find_time(html)
				the_username = self.find_username(html)
				the_reponame = self.find_reponame(html)
				for j in range(0,len(the_url)):
					tur.append(the_time[j]+"="+the_username[j]+"="+the_reponame[j])
				for u in the_url:
					result[u] = tur[t]
					t=t+1
			else:
				print "No."+str(i)+" is None!!!"
		print "finish result!!!"
		print result		
		try:
			print "check whitelist..."
			cur = conn.cursor()
			sql = "select url from result where is_white=1;"
			n = cur.execute(sql)
			row = int(cur.rowcount)
			for x in range(0,row):
				whitelist.append(cur.fetchone())
			cur.close()
			conn.commit()
		except Exception,e:
			print e
			conn.rollback()
		for k in result.keys():
			print k
			print result[k]
			ti,un,rn = result[k].split("=")
			try:
				cur = conn.cursor()
				sql = "update result set username='"+un+"',reponame='"+rn+"' where url='"+k+"';"
				n = cur.execute(sql)
				cur.close()
				conn.commit()
				print "update ok!!!"
			except Exception,e:
				print e
				conn.rollback()

			if k in whitelist:
				print "in white!!!"
			else:
				print "not in whitelist!!!"
				try:
					print "check new..."
					cur = conn.cursor()
					sql = "select count(*) from result where url='"+k+"';"
					n = cur.execute(sql)
					count = cur.fetchall()
					cur.close()
					conn.commit()
					if count[0][0] == 0:
						print "find new!!!"
						try:
							print "insert new into db..."
							cur = conn.cursor()
							sql = "insert into result (url,keyword,time,is_del,is_white,username,reponame) values (%s,%s,%s,%s,%s,%s,%s);"
							param = (k,self.key,ti,0,0,un,rn)
							n = cur.execute(sql,param)
							cur.close()
							conn.commit()
							print "insert new done!!!"
						except Exception,e:
							print e
							conn.rollback()
					else:
						print "check is_del..."
						try:
							cur = conn.cursor()
							sql = "select is_del from result where url = '"+k+"';"
							n = cur.execute(sql)
							cc = cur.fetchall()
							print cc
							c = cc[0][0]
							cur.close()
							conn.commit()
						except Exception,e:
							print e
							conn.rollback()
						if c == 1:
							try:
								cur = conn.cursor()
								sql = "update result set is_del=0 where url='"+k+"';"
								n = cur.execute(sql)
								cur.close()
								conn.commit()
							except Exception,e:
								print e
								conn.rollback()
						print "check is_del done!!!"
						print "check if is new update..."
						new_time = filter(str.isdigit,ti)
						try:
							cur = conn.cursor()
							sql = "select time from result where url ='"+k+"';"
							n = cur.execute(sql)
							cc = cur.fetchall()
							c = cc[0][0]
							old_time = filter(str.isdigit,c)
							cur.close()
							conn.commit()
						except Exception,e:
							print e
							conn.rollback()
						if new_time > old_time:
							try:
								print "is new update!!!"
								print "update the db..."
								cur = conn.cursor()
								sql = "update result set time=new_time where url='"+k+"';"
								n = cur.execute(sql)
								cur.close()
								conn.commit()
								print "update the db done!!!"
							except Exception,e:
								print e
								conn.rollback()
						else:
							print "is not new update!!!"
				except Exception,e:
					print e
					conn.rollback()		

						
		#result no db yes
		try:
			"check del..."
			dburl = list()
			cur = conn.cursor()
			sql = "select url from result where is_del=0 and is_white=0 and keyword='"+self.key+"';"
			n = cur.execute(sql)
			dburl = cur.fetchall()
			cur.close()
			conn.commit()
		except Exception,e:
			print e
			conn.rollback()
		ccc = 0
		for d in dburl:
			for dd in d:
				if dd in result.keys():
					print "no del!!!"
				else:
					ccc = ccc+1
					print "del!!!"
					try:
						print "update del to db..."
						cur = conn.cursor()
						sql = "update result set is_del=1 where url='"+dd+"';"
						n = cur.execute(sql)
						cur.close()
						conn.commit()
						print "update del done!!!"
					except Exception,e:
						print e
						conn.rollback()
		print "ccc="+str(ccc)


		
if __name__ == '__main__':
	print "githubscan start..."
	
	for kw in keyword:
		gs = githubscan(kw)
		gs.run()
	print "githubscan done!!!"




import urllib
import urllib2
import string
import re
import time
import redis
import MySQLdb


w = list()
conn = MySQLdb.connect(host='localhost',port=8999,user='wei',passwd='hehe',db='github')
keyword = ["xxx"]
whitelist = []
user_agent = "User-Agent: Mozilla/5.0 (Windows NT 6.3; WOW64; rv:35.0) Gecko/20100101 Firefox/35.0 security_test"
class githubscan:
	def __init__(self,key):
		self.key = key
	def send(self,t):
		target = t
		print target
		try:
			req = urllib2.Request(target)
			req.add_header('User-Agent',user_agent)
			rep = urllib2.urlopen(req)
			httpcode = rep.getcode()
			html = rep.read()
			return html
		except Exception,e:
			print e
			return None
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

	def find_name(self,s):
		m1 = re.findall(r'</a>\n       &#8211;',s)
		m2 = re.findall(r'</a> <br>\n      <span class="text-small text-muted match-count">',s)
		if m1 and m2:
			name = list()
			i = 0
			for n in m1:
				na = n+"-"+m2[i]
				i = i + 1
				name.append(na)
		else:
			print "name is none!!!"
		return name

	def run(self):
		the_url = list()
		the_time = list()
		the_name = list()
		result = dict()
		target1 = "https://github.com/search?&q="+self.key+"&type=Code"
		html1 = self.send(target1)
		print "get total page num..."
		page_num = self.find_count(html1)
		print "get total num done!!!"
		print "send each request..."
		for i in range(1,page_num+1):
			target = "https://github.com/search?p="+str(i)+"&q="+self.key+"&ref=searchresults&type=Code"
			time.sleep(5)
			html = self.send(target)
			if html is not None:
				the_url = self.find_url(html)
				the_time = self.find_time(html)
				t = 0
				for u in the_url:
					result[u] = the_time[t]
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
							sql = "insert into result (url,keyword,time,is_del,is_white) values (%s,%s,%s,%s,%s);"
							param = (k,self.key,result[k],0,0)
							n = cur.execute(sql,param)
							cur.close()
							conn.commit()
							print "insert new done!!!"
						except Exception,e:
							print e
							conn.rollback()
					else:
						print "check if is new update..."
						new_time = filter(str.isdigit,result[k])
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




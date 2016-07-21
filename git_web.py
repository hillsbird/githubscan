import web
import githubscan
import MySQLdb
from web import form

urls=(
'/','index',
)
data1 = ""
info = ""
render = web.template.render('templates')
conn = MySQLdb.connect(host='localhost',port=8999,user='wei',passwd='hehe',db='github')

class index:
        def GET(self):
                try:
                        cur = conn.cursor()
                        sql = "select * from result where is_del=0 and is_white=0;"
                        n = cur.execute(sql)
                        data = cur.fetchall()
                        cur.close()
                        conn.commit()
#			print data
                except Exception,e:
                        print e
                        conn.rollback()
		return render.index(data,info)
	def POST(self):
		the_input = web.input()
		if len(the_input.name) == 0:
			info = "please add whitelist!"
			print info
		else:
			print type(the_input.name)
			print the_input.name
			urls = str(the_input.name)
			theurls = urls.split(",")
			for n in theurls:
				try:
                                	print "add whitelist..."
					print n
                                	cur = conn.cursor()
                                	sql = "update result set is_white=1 where url='"+n+"';"
                                	n = cur.execute(sql)
                                	cur.close()
                                	conn.commit()
					info = "add whitelist success!!!"
                                	print "add whitelist done!!!"
                        	except Exception,e:
					info = e
                                	print e
                                	conn.rollback()
                return render.index(data1,info)

app = web.application(urls,globals())

if __name__ == '__main__':
	app.run()

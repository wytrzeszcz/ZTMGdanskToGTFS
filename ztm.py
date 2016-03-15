import os
import csv 
import string
import StringIO
import re
import time
from datetime import datetime

from os.path import join, getsize

start_path='./data'

def time_formater (hour,minute,zero_couter):
	"""create string with time, egarding that i base we can go in 0 minutes betwen """
	ret=''

	if (hour<10):
		ret=ret+"0"
	ret=ret+str(hour)+":"
	if(minute <10):
		ret=ret+"0"
	ret=ret+str(minute)
	s1=zero_couter*2
	s2=zero_couter*2+1
	if(s1<10):
		ss1="0"+str(s1)
	if(s2<10):
		ss2="0"+str(s2)

	ret=ret+":"+ss1+","+ret+":"+ss2
	return ret

def make_calendar ():
	calendar= open('calendar.txt','w')
	calendar.write( "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n")
	for lines  in os.listdir(start_path):
		line_number=lines[:3] 
		date=lines[4:12]
		calendar.write( lines+"P,1,1,1,1,1,0,0,"+date+",20220923\n")
		calendar.write( lines+"S,0,0,0,0,0,1,0,"+date+",20220923\n")
		calendar.write( lines+"N,0,0,0,0,0,0,1,"+date+",20220923\n")
	calendar.close()


def make_routes ():
	routes= open('routes.txt','w')
	#here i need to change print to route.write ()
	routes.write('route_id,route_short_name,route_long_name,route_type\n')
	for lines  in os.listdir(start_path):
		variants1=next(csv.reader(open(start_path+"/"+lines+"/"+lines+"warianty1.csv",'rb'),delimiter=";"))
		variants2=next(csv.reader(open(start_path+"/"+lines+"/"+lines+"warianty2.csv",'rb'),delimiter=";"))	
		for variant_id in variants1[4:] :
			if  variant_id.replace('(00:00-29:59)','')!='' : 
 				routes.write(lines[:3]+"_"+variant_id.replace('(00:00-29:59)','')+',,'+lines[:3]+"_"+variant_id.replace('(00:00-29:59)','')+',0\n') #empty string at short name
		for variant_id in variants2[4:] :
			if  variant_id.replace('(00:00-29:59)','')!='' : 
				routes.write(lines[:3]+"_"+variant_id.replace('(00:00-29:59)','')+',,'+lines[:3]+"_"+variant_id.replace('(00:00-29:59)','')+',0\n') #emptystring at short name
	routes.close()


def make_kurs(): #translate
	kursy_tmp= open('tmp_kursy.txt','w')
	day_sign='P'
	for lines  in os.listdir(start_path):
		kursy1=csv.reader(open(start_path+"/"+lines+"/"+lines+"kursy1.csv",'rb'),delimiter=";")
		kursy2=csv.reader(open(start_path+"/"+lines+"/"+lines+"kursy2.csv",'rb'),delimiter=";")	
		for kurs in kursy1 :
			if (kurs[0]=='99'): #if we got 99 we can detect what day is it
				if (kurs[1][0]=='D'): ## Translate from those format to our format of day sign 
					day_sign='P'  
				if (kurs[1][0]=='S'):
					day_sign='S'
				if(kurs[1][0]=='N'):
					day_sign='N'
			else:
				#print kurs
				kursy_tmp.write( kurs[0]+","+kurs[1]+","+day_sign+','+lines[:3]+'\n' )
		for kurs in kursy2 :
			if (kurs[0]=='99'):
				if (kurs[1][0]=='D'): ## kononczys tu robie oznaczenie dnia ktore bedzie trzecia kolumna 
					day_sign='P'  
				if (kurs[1][0]=='S'):
					day_sign='S'
				if(kurs[1][0]=='N'):
					day_sign='N'
			else:
				#print kurs
				kursy_tmp.write(kurs[0]+","+kurs[1]+","+day_sign+','+lines[:3]+"\n")
	#kursy_tmp.close()

def make_trips():
	trips=open('./trips.txt','w')
	trips.write("route_id,service_id,trip_id\n")
	routes=csv.reader(open('routes.txt','rb'),delimiter=',')
	routes.next()
	for route in routes:		
		calendar=csv.reader(open('calendar.txt','rb'),delimiter=',')
		calendar.next()
		for cal in calendar:
			kursy=csv.reader(open('./tmp_kursy.txt','rb'),delimiter=',')
			for kurs in kursy:
				if (route[0][:3]==kurs[3] and route[0][4:]==kurs[1] and cal[0][-1:]==kurs[2] and cal[0][:3]==kurs[3]) :
					trips.write(route[0]+','+cal[0]+','+route[0]+'-'+kurs[0]+'-'+cal[0]+"\n")
	trips.close()

def make_stop_times():
	print "wchodze"
	stop_times=open('stop_times.txt','w')
	stop_times.write("trip_id,arrival_time,departure_time,stop_id,stop_sequence\n")
	trips=csv.reader(open('./trips.txt','rb'),delimiter=',')
	trips.next()
	for trip in trips:
		variantX=re.sub(r'.*(X[0-9]*).*', r'\1', trip[2])
		line=re.sub(r'.*[^0-9]([0-9]{3})[^0-9].*', r'\1', trip[2])
		start_time=re.sub(r'.*([0-9][0-9]:[0-9][0-9]).*', r'\1', trip[2])	
		folder=re.sub(r'.*-([0-9]{3}_[0-9]{8}_?[0-9]?).*', r'\1', trip[2])
		variants1=csv.reader(open(start_path+"/"+folder+"/"+folder+"warianty1.csv",'rb'),delimiter=';')
		head=variants1.next()
		col=0
		for i in xrange(4,len(head)):
			if(variantX+"(00:00-29:59)"==head[i]):
				col=i
				break
		if (col!=0): #zero mean we dont find any mach
			travel_time=0
			zero_couter=0
			for variant in variants1 :
				
				if (variant[col]!=''):
					if int(variant[col]) == 0 : #dirty hack for search 2 zero times runS
						zero_couter=zero_couter+1
					travel_time=travel_time+int(variant[col])
					hour=int(re.sub(r"([^:]*):.*",r'\1',start_time))
					minute=int(re.sub(r".*:(.*)",r'\1',start_time))
					minute=minute+travel_time
					while (minute>=60):
						minute=minute-60
						hour=hour+1
					stop=re.sub(r".*[^0-9]([0-9]{3,4})[^0-9].*",r'\1',variant[1])
					stop_times.write(trip[2]+','+time_formater(hour,minute,zero_couter)+','+stop+','+variant[0]+'\n')
					last=int(variant[col])
					#print variant[0]+"\t"+variant[1]+" -"+stop+"-\t"+variant[col]+"\t"+str(hour)+":"+str(minute)+"\t"+variantX+"\t"
		variants2=csv.reader(open(start_path+"/"+folder+"/"+folder+"warianty2.csv",'rb'),delimiter=';')
		head=variants2.next()
		#print head
		col=0
		for i in xrange(4,len(head)):
			if(variantX+"(00:00-29:59)"==head[i]):
				col=i
				break
		#print str(col)+" "+variantX
		if (col!=0): #zero mean we dont find any mach
			travel_time=0
			zero_couter=0
			for variant in variants2:
				if (variant[col]!=''):
					if  int(variant[col]) == 0 : #dirty hack for search 2 zero time runs
						zero_couter=zero_couter+1
					#print variant[0]+" "+variant[1]+" "+variant[col]
					travel_time=travel_time+int(variant[col])
					hour=int(re.sub(r"([^:]*):.*",r'\1',start_time))
					minute=int(re.sub(r".*:(.*)",r'\1',start_time))
					minute=minute+travel_time
					while (minute>=60):
						minute=minute-60
						hour=hour+1
					stop=re.sub(r".*[^0-9]([0-9]{3,4})[^0-9].*",r'\1',variant[1])
					stop_times.write(trip[2]+','+time_formater(hour,minute,zero_couter)+','+stop+','+variant[0]+'\n')
					
					last=int(variant[col])
	stop_times.close()

make_kurs()
print "kursy_tmp.txt\t done"
make_calendar()
print "calenar.txt\t done"
make_routes()
print "routes.txt\t done"
make_trips() #no drugs
print "trips.txt\t done"
make_stop_times()
print "stoptimes.txt\t done"

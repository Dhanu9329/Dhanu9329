import can
import cantools
import time
import openpyxl

##path = "tracker_format.xlsx"
##wb_obj = openpyxl.load_workbook(path)

st = time.time()

##IDB
diag_req_id=0x6A9
diag_res_id=0x629
##
###RCU
#diag_req_id=0x6A7
#diag_res_id=0x627
######
####EPS1
##diag_req_id=0x6A8
##diag_res_id=0x628
####
######EPS2
##diag_req_id=0x6AB
##diag_res_id=0x62B
    
####EASC
##diag_req_id=0x6AE
##diag_res_id=0x62E
##
##


DID_List_To_Read={0xF18C:0xa,
                  0xF101:0,
                  0xF103:3,0xF143:0,
                  0xF188:3,0xF148:0,
                  0xF102:3,0xF142:0,
                  0xF191:0x3,0xF141:0,
                  0xF190:0xa,
                  0xF192:0xa,
                  0xF194:0xa,
                  0xF110:0xa,
                  0xF18F:0xa
                  }##key value 3->first bytes ascii sym, 0xa-> all symbols, 0->all in bytes


#DID_List_To_Read={0xF188:3,0xF142:0,0xF102:3,0xF101:0,0xF110:0xa,0xF148:0,0xF18C:0xa,0xF103:3,0xF141:0,0xF143:0,0xF191:0x3}##key value 3->first bytes ascii sym, 0xa-> all symbols, 0->all in bytes


filters = [
    {"can_id": diag_req_id, "can_mask":0x7FF, "extended": False},
    {"can_id": diag_res_id, "can_mask":0x7FF, "extended": False},
]

#bus = can.interface.Bus(bustype='vector', channel=0, bitrate=500000,
#                         app_name='python')#,can_filters=filters)

#db = cantools.database.load_file('07_PT_CAN_Matrix_BEV_V9.2.1.dbc')
#IDB_req = db.get_message_by_frame_id(0x6A7)



message = can.Message(arbitration_id=diag_req_id, data=[0x3,0x22,0xF1,0x88,0x55,0x55,0x55,0x55],is_extended_id=False)
read_flow_control = can.Message(arbitration_id=diag_req_id, data=[0x30,0x00,0x00,0x00,0x00,0x00,0x00,0x00],is_extended_id=False)

def read_DID(did_read):
    global resp_string
    global resp_buff
    resp_buff=[]
    resp_string=""
    global multi_frame
    global single_frame
    multi_frame=False
    single_frame=False
    DID_byte_1=int((did_read&0xFF00)/0x100)
    DID_byte_0=int((did_read&0x00FF))
    resp_buff=[]
    message = can.Message(arbitration_id=diag_req_id, data=[0x3,0x22,DID_byte_1,DID_byte_0,0x55,0x55,0x55,0x55],is_extended_id=False)
    
    #bus.recv(5)
    bus.send(message)
    
    
    i=0
    first_frame_flag=0
    length_loop=0
    mf=-1
    first_loop=0
    global st_t
    st_t=time.time()
    for msg in bus:
        
        i+=1
        #print(i,hex(msg.arbitration_id))
        if(i>5000):
            print("no response in last 5000 messages received")
            break
        if(msg.arbitration_id==diag_res_id):
            i=0
            if(0==first_loop):
                first_loop+=1
                if(0x10==msg.data[0]&0xF0):
                    #print("first frame")
                    multi_frame=True
                    bus.send(read_flow_control)
                    first_frame_flag=1
                    length_of_canframe=(msg.data[0]&0x0F)*0x100+msg.data[1]
                    length_loop=length_of_canframe+2
                    #print("ini lenght",hex(did_read)," ",length_loop)
                else:
                    #print("single frame")
                    single_frame=True
                    length_of_canframe=msg.data[0]+1
                    length_loop=length_of_canframe

                

            if((first_frame_flag) and (0x20==msg.data[0]&0xF0)):
                #print("at second frames")
                length_loop+=1#msg.data[0]&0x0F
                #print("extd lenght ",hex(did_read)," ",length_loop)

            resp_string=resp_string+msg.data.hex()+" "
            mf=0
            for d in msg.data:
                mf+=1
                resp_buff.append(d)
                length_loop-=1
                #print(hex(did_read),"" ,length_loop," ",d)
                if(0==length_loop):
                    #print("res time",hex(did_read),st_t-time.time())
                    return



def checkNRC(resp_buff1):
    if(0x7F==resp_buff1[1]):
        print("NRC:",hex(resp_buff1[3]), nrc_table[resp_buff1[3]],"For service",hex(resp_buff1[2]))
    else:
        print(resp_string)
        

def reponse_data_cvd(resp_buff1,u):
    l=0
    resp_data=""
    #print(resp_buff1)
    if(""==resp_buff1):
        "print no response"
    elif(0x7F==resp_buff1[1]):
        print("negative response data:",resp_string)
        resp_data="NRC:"+hex(resp_buff1[3])+nrc_table[resp_buff1[3]]
    elif(3==u):
        for a in resp_buff1:    
            l+=1
            if( 5<l<9):
                resp_data=resp_data+chr(a)
                
            elif(l>9):
                resp_data=resp_data+str('{:02X}'.format(a))
    elif(0==u):
        for a in resp_buff1:
            l+=1            
            if(4<l):                
                if(0==a):
                    resp_data=resp_data+str(a)
                resp_data=resp_data+str('{:02X}'.format(a))

    elif(0xa==u):
        for a in resp_buff1:
            l+=1
            if(single_frame and 4<l):
                resp_data=resp_data+chr(a)
                if(0==a):
                    resp_data='0'+resp_data

            elif(multi_frame and (5<l) and (l!=9)and (l!=17)):
                resp_data=resp_data+chr(a)
##                if(0==a):
##                    resp_data='0'+resp_data
                    

        
    else:
        resp_data=resp_string
         
    return(resp_data)
                                    


##with can.interface.Bus(bustype='vector', channel=0, bitrate=500000,app_name='python') as bus:
with can.interface.Bus(bustype='vector', channel=0, bitrate=500000,app_name='eMIDAS') as bus:
    for did,value in DID_List_To_Read.items():
        read_DID(did)
        format_output=reponse_data_cvd(resp_buff,value)
        print('{:02X}'.format(did),": ",format_output,end="\n")
       ## checkNRC(resp_buff)
        ##print(resp_string)




et = time.time()
elapsed_time = et - st
print('Run time of the code:', elapsed_time, 'seconds')

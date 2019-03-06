import psycopg2 as rs
import boto
import pandas as pd
from config_file import file_bucket
from config_file import temp_s3_bucket
from config_file import schema
from config_file import dbname
from config_file import port
from config_file import user
from config_file import password
from config_file import table_name
from config_file import host_url
from config_file import aws_access_key_id
from config_file import aws_secret_access_key
from config_file import incremental_load

"""
# If incremental load = "Y"
#take latest file from bucket and place it temp directory

if incremental_load = "Y":
	take latest file from s3 bucket and place in temp directory
else:
    place all files from rawdata to temp directory

for all files in temp_directory
	opton 1 : load json file in redshift directly
    option 2 : convert json in to csv using pandas and load it to redshift for each csv file
    
delete all json files from temp_directory

"""


# Connecting to S3 and listing all files

s3_client = boto.connect_s3( 
                      aws_access_key_id=aws_access_key_id, 
                      aws_secret_access_key=aws_secret_access_key, 
                      
                      )

file_bucket = s3_client.get_bucket(file_bucket)
sub_bucket_files = file_bucket.list(file_bucket+'/20') # we are excluding temp sirectory and limiting only directories json files
l = [(file.last_modified, file) for file in sub_bucket_files] # taking file name and timestamp from file listing data

if incremental_load == "Y": #if incremental load, take latest file and place on temp directory
    latest_file_name = sorted(l, lambda x,y: (x[0], y[0]))[-1][1] #sorted based on 2nd timestamp attribute and extracting latest one
    latest_file_name.get_contents_to_filename(temp_s3_bucket + latest_file_name) # placing it on temp directory

else: #take all files and place in temp directory
    for file in l:
        file[1].get_contents_to_filename(temp_s3_bucket + latest_file_name) # copying all files in temp directory for load


# get list of files which are placed in tempdirectory
target_bucket = s3_client.get_bucket(temp_s3_bucket)

for file_path in bucket.list():
    
        #option 1: load json file directly in redshift
        # json file can be loaded in redshift 

        sql="""copy {}.{} 
                from '{}'\
             credentials \
            'aws_access_key_id={};
            aws_secret_access_key={}' \
            JSON 'auto' ACCEPTINVCHARS;commit;"""\
             .format(schema, table, file_path, aws_access_key_id, aws_secret_access_key)

        con_url = "dbname='{}'\
                    port='{}' \
                    user='{}' \
                    password='{}' \
                    host='{}'"\
                  .format(dbname,port,user,password,host_url)  

        con = rs.connect(con_url)

        cursor = con.cursor()
        cursor.execute(sql)
        cursor.close()

    
    # Option 2 
    #convert json file to csv using pandas
    
    df = pd.read_json(file_path) # reading json file
    df.to_csv(file_path) #writing in csv file
    
    #load data in redshift
    
    sql="""copy {}.{} 
                from '{}'\
             credentials \
            'aws_access_key_id={};
            aws_secret_access_key={}' \
            DELIMITER ',' ACCEPTINVCHARS;commit;"""\
             .format(schema, table, file_path, aws_access_key_id, aws_secret_access_key)

    con = rs.connect(con_url)

    cursor = con.cursor()
    cursor.execute(sql)
    cursor.close()
	
#delete temp_directory

for file_path in bucket.list():
    bucket.delete_key(file_path)

		
		

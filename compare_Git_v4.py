from ctypes import sizeof
import json
from turtle import update
from deepdiff import DeepDiff
import csv
from pathlib import Path
import pandas as pd
from git import Repo
import shutil
import os
import stat
from os import path
import datetime

def getFilename(filename):
     filename=filename.split('.') #Recupère le nom de fichier
     return filename[0]

def getPath(p,id,name): # Donne le chemin des données modifiées dans le fichier JSON
    list= p.split("][")
   
    list[0]=str(list[0])[len(str(list[0]))-1]
    list[len(list)-1]= list[len(list)-1][:-1] + "'"
    list[1]=name+"/"+id
    
    new_path=""
    
    for l in list[1:]:
            new_path=new_path + str(l)
    new_path=new_path.replace("''","/")
    new_path=new_path.replace("'","/")

    return new_path

def getInfo(updated, removed,added, csvName, actual_dir, jsonName,idName):# Recupère ligne à ligne les informations qui ont été modifiées
    print(csvName)
    update = []
    add = []
    remove= []
    nb_update,nb_added,nb_remove = 0,0,0
    for key in list(updated.keys()):
        #nb_update= len(updated[key]['values_changed'])
        for object in updated[key]['values_changed']:
            new_value, old_value =updated[key]['values_changed'][object]['new_value'], updated[key]['values_changed'][object]['old_value']
            path=getPath(object,key,idName)
            update.append([path,'UPDATE',old_value,new_value])
            nb_update=nb_update+1
    for key in list(removed.keys()):
        removed_value= removed[key]
        remove.append([key,'REMOVED',removed_value])
        nb_remove= nb_remove +1
        
    for key in list(added.keys()):
            added_value= added[key]
            add.append([key,'ADDED',added_value])
            nb_added= nb_added+1
    
    
    with open(actual_dir +"/"+csvName, 'w', newline='') as file: #creation csv
        writer = csv.writer(file)
       
        if nb_update!=0:
            writer.writerow(["Path", "Change type", "Old Value","New Value"])
            for i in range(nb_update):
                writer.writerow([update[i][0], update[i][1], update[i][2],update[i][3]])
        if nb_added !=0 :
            writer.writerow(["ID", "Change type", "New Value"])
            for i in range(nb_added):
                writer.writerow([add[i][0], add[i][1], add[i][2]])
        if nb_remove !=0 :
            writer.writerow(["ID", "Change type", "Old Value"])
            for i in range(nb_remove):
                writer.writerow([remove[i][0], remove[i][1], remove[i][2]])
       
        file.close()   

    with open(actual_dir+ "/" +jsonName, 'w', encoding='utf-8') as jsonf: # crétaion JSON
        jsonArray=[]
        if nb_update!=0:
            for i in range(nb_update):
                name=update[i][0].split('/')[len(update[i][0].split('/'))-2]
                jsonArray.append({"Path":update[i][0],"Change type":update[i][1], "Old Value": [name ,update[i][2]],"New Value": [name, update[i][3]]})
                
        if nb_added !=0 :
            for i in range(nb_added):
                jsonArray.append({"ID":add[i][0],"Change type":add[i][1],"New Value": add[i][2]})
                
            
        if nb_remove !=0 :
            for i in range(nb_remove):
                jsonArray.append({"ID":remove[i][0],"Change type":remove[i][1],"Old Value": remove[i][2]})

        jsonString = json.dumps(jsonArray, indent=4)
        jsonf.write(jsonString)        
        
    
   
    
    return nb_update,nb_added,nb_remove

def cleanDirectory(directory):#Nettoie les dossiers 
    if(os.path.exists(directory)):
        for root, dirs, files in os.walk(directory):  
            for d in dirs:
                os.chmod(path.join(root, d), stat.S_IRWXU)
            for file in files:
                os.chmod(path.join(root, file), stat.S_IRWXU)
        shutil.rmtree(directory)

def getId(old_d):
    id=""
    for object in old_d:
        keys= list(object.keys())
        for i in range(len(keys)-1):
            if 'id' in keys[i] or 'Id' in keys[i]:
                return keys[i]
    return id

#Récupération des deux versions de la backup sur git Hub
gitRepo = input("Renseigner l'address du repositori : ")

while(bool(gitRepo.strip() )==False):
    print('Merci de rentrer une addresse de repositori')
    gitRepo = input("Renseigner l'address du repositori : ")
    
gitRepo="https://github.com/NinaNedjar/test_git.git"  # address du repo  A SUPRIMER


dir= os.getcwd()+ "\Backup"


#Récupération des numéros de commit
print('Si vous ne rentrez aucune valeur pour les commit, les valeurs par défault seront les deux derniers commits : ')
last_commit= input("Renseigner le numéros de commit numéros 1 (la valeur par default étant le dernier commit) : ")
second_commit= input("Renseigner le numéros de commit numéros 2 (la valeur par default étant l'avant dernier commit) : ")
print()

#Chemin pour stocker les données
new_dir=dir+"/new"
old_dir=dir+"/old"
actual_dir= dir+"/actual"

#Nettoyage des dossiers précedents

cleanDirectory(new_dir)
cleanDirectory(old_dir)
cleanDirectory(actual_dir)

#Telechargement des donnée de git
new_repo =Repo.clone_from(gitRepo,new_dir)
old_repo =Repo.clone_from(gitRepo,old_dir)
actual_repo =Repo.clone_from(gitRepo,actual_dir)

new_repo_git= new_repo.git
old_repo_git=old_repo.git
actual_repo_dir=actual_repo.git

#Recuperation des 2 derniers commit
commits = list(old_repo.iter_commits('main', max_count=2))

if(bool(last_commit.split())==False):
    last_commit=commits[0]
if(bool(second_commit.split())==False):
    second_commit=commits[1]

#Checkout sur les commits indiqués
new_repo_git.checkout(last_commit) # version plus récente
old_repo_git.checkout(second_commit) # version plus ancienne

#FAIRE LA COMPARAISON 

#Chemin des dossiers où sont stockées les informations
new_dir=new_dir+"/JSONFromTalend"
old_dir=old_dir+"/JSONFromTalend"
if os.path.exists(actual_dir+'/ChangeReport'):
    cleanDirectory(actual_dir+'/ChangeReport')
d= str(datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S'))
if not os.path.exists(actual_dir+'/Backup'):
 os.makedirs(actual_dir+'/Backup')
os.makedirs(actual_dir+'/Backup/' + d)
actual_dir=actual_dir+'/Backup/' +d
jsonRepport=[]


for filename in os.listdir(old_dir): 
    old_file = os.path.join(old_dir,filename)
    new_file = os.path.join(new_dir,filename)

    
    if( os.stat(old_file).st_size == 0 or os.stat(new_file).st_size == 0): #Si on a une dossier vide
        if ( len(old_file) > len(new_file)) :
            nbObject= len(old_file)
            print("CHANGE IN FILE  " + str(nbObject) + " contenu effacé" )
            changeType="Suppression"
            jsonRepport.append({'File Name': filename,'Change type': changeType,'Number of lines concerned': str(nbObject)})
                
        elif ( len(old_file) < len(new_file)) :
            nbObject= len(new_file)
            print("CHANGE IN FILE  " + str(nbObject) + " contenu ajouté")
            changeType="Addition"
            jsonRepport.append({'File Name': filename,'Change type': changeType,'Number of lines concerned': str(nbObject)})
        
    else: # si les deux dossiers on des données

        with open(old_file) as json1:
            old_data = json.load(json1)
        with open(new_file) as json2:
            new_data = json.load(json2)
        
        csvName = getFilename(filename) + '.csv'
        jsonName = getFilename(filename) + '.json'
        if DeepDiff(old_data,new_data)!={}: # si différence entre les 2 fichiers JSON
            print(filename)
            id= getId(old_data) # recup de l'id de l'object
            list_old_id={}
            list_new_id={}
            for data in old_data:
                old_id=data[id]
                list_old_id[old_id]=data
            for d in new_data:
                new_id=d[id]
                list_new_id[new_id]=d
            updated={}
            removed={}
            added={}
            for k in list(list_old_id.keys()): # trie les data si il y a eu update ou removed ou added
                if k in list_new_id:
                    if(DeepDiff(list_old_id[k],list_new_id[k])!={}):
                        updated[k]=DeepDiff(list_old_id[k],list_new_id[k])
                    list_new_id.pop(k)
                    list_old_id.pop(k)
                
            removed= list_old_id
            added= list_new_id
            
            nbLigne,nbObjectAdded,nbObjectRemoved = getInfo(updated,removed,added,csvName,actual_dir,jsonName,id) 
            
          
            jsonRepport.append({'File Name': filename,'Update':  nbLigne,'Addition': nbObjectAdded,'Suppresion': nbObjectRemoved})
           
with open(actual_dir + '/' + 'Report.json', 'w') as outfile:
    json.dump(jsonRepport,outfile, indent=4)

#Push du report sur Git
"""
actual_repo.git.add(all=True)
actual_repo.index.commit("Backup report : " + datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S') )
origin = actual_repo.remote(name='origin')
origin.push()
"""

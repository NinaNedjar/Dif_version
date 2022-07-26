import os
import sys
import json
import datetime

#report_file= sys.argv[1] décomenter pour faire le lien avec l'autre script
#report_file= "C:/Users/nined/OneDrive\Documents/SHAPLE/Git_versioning/test_alerting/change_1"
#report_file= "C:/Users/nined/OneDrive\Documents/SHAPLE/Git_versioning/test_alerting/no_change"
report_file="C:/Users/nined/OneDrive\Documents/SHAPLE/Git_versioning/test_alerting/change_MFA"
dir="C:/Users/nined/OneDrive\Documents/SHAPLE/Git_versioning/test_alerting"
#print(sys.argv)


with open(report_file + '/' + 'Report.json', 'r') as file: #Recupère le fichier de report pour vérifier si des changement on eu lieu
   report= json.load(file)
   file.close()
print(report)

config_file= "C:/Users/nined/OneDrive\Documents/SHAPLE/Git_versioning/test_alerting/config.json"
with open(config_file , 'r') as conf: 
   configs= json.load(conf)
   conf.close()

if len(report) != 0:
    d= str(datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S'))
    if not os.path.exists(dir+'/Alerte'): #créer dossier alert si n'existe pas
        os.makedirs(dir+'/Alerte')
    dir_alerte=dir+'/Alerte/' + d
    os.makedirs(dir_alerte)

    filtres={}
    for i in configs:  #" Recuperer les filtres"
        filtres[i["Titre"]]=i["Filtre"]

    filename=[]
    for i in report: # récupérer les nom des dossiers changés
        filename.append(i['File Name'])
    # créer dossier en fonction des types d'alerte

    for config in configs:
        """
        if '' in config['Filtre']:
            print("ALL change")
            with open(dir_alerte+ "/" + config['Titre']  +".json", 'w', encoding='utf-8') as jsonf:
                jsonArray=[]
                
                for i in filename:
                    print(config['Body'])
                    config['Body']=config['Body'] + " " + i
                    print(config['Body'])
                alert={'Destinataire': config['Destinataire'],'Body': config['Body'] }
                print(alert)
                jsonArray.append(alert)
                jsonString = json.dumps(jsonArray, indent=4)
                jsonf.write(jsonString)
"""
        for filtre in config['Filtre']:
            for name in filename:
                alert={}
                if str(filtre) in name :
                    with open(dir_alerte+ "/" + config['Titre']  +".json", 'w', encoding='utf-8') as jsonf:
                        jsonArray=[]
                        alert={}
                        config['Body']=config['Body']+ " " + name
                            
                        alert={'Body': config['Body'] }
                        print(alert)
                        jsonArray.append(alert)
                        jsonString = json.dumps(jsonArray, indent=4)
                        jsonf.write(jsonString)
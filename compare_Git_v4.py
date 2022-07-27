import csv
import datetime
import shutil
import stat
from os import path

from deepdiff import DeepDiff

from util.Backupta import *

DEFAULT_WORKSPACE = os.getenv("DEFAULT_WORKSPACE", "./workspace")
backup = os.getenv('BACKUP_DIRECTORY', '/Backup')
new_d = os.getenv('NEW_BACKUP_DIRECTORY', '/new')
old = os.getenv('OLD_BACKUP_DIRECTORY', '/old')
current = os.getenv('CURRENT_BACKUP_DIRECTORY', '/current')
jsonFromTalend = os.getenv('CONFIG_DIRECTORY', '/JSONFromTalend')

REPORT = "/Report.json"


def getFilename(filename):
    filename = filename.split('.')  # Recupère le nom de fichier
    return filename[0]


def getPath(p, id, name):  # Donne le chemin des données modifiées dans le fichier JSON
    list = p.split("][")

    list[0] = str(list[0])[len(str(list[0])) - 1]
    list[len(list) - 1] = list[len(list) - 1][:-1] + "'"
    list[1] = name + "/" + id

    new_path = ""

    for l in list[1:]:
        new_path = new_path + str(l)
    new_path = new_path.replace("''", "/")
    new_path = new_path.replace("'", "/")

    return new_path


def getInfo(updated, removed, added, csvName, actual_dir, jsonName,
            idName):  # Recupère ligne à ligne les informations qui ont été modifiées
    update, add, remove = [], [], []
    nb_update, nb_added, nb_remove = 0, 0, 0
    for key in list(updated.keys()):
        for object in updated[key]['values_changed']:
            new_value, old_value = updated[key]['values_changed'][object]['new_value'], \
                                   updated[key]['values_changed'][object]['old_value']
            path = getPath(object, key, idName)
            update.append([path, 'UPDATE', old_value, new_value])
            nb_update = nb_update + 1
    for key in list(removed.keys()):
        removed_value = removed[key]
        remove.append([key, 'REMOVED', removed_value])
        nb_remove = nb_remove + 1

    for key in list(added.keys()):
        added_value = added[key]
        add.append([key, 'ADDED', added_value])
        nb_added = nb_added + 1

    with open(actual_dir + "/" + csvName, 'w', newline='') as file:  # creation csv
        writer = csv.writer(file)

        if nb_update != 0:
            writer.writerow(["Path", "Change type", "Old Value", "New Value"])
            for i in range(nb_update):
                writer.writerow([update[i][0], update[i][1], update[i][2], update[i][3]])
        if nb_added != 0:
            writer.writerow(["ID", "Change type", "New Value"])
            for i in range(nb_added):
                writer.writerow([add[i][0], add[i][1], add[i][2]])
        if nb_remove != 0:
            writer.writerow(["ID", "Change type", "Old Value"])
            for i in range(nb_remove):
                writer.writerow([remove[i][0], remove[i][1], remove[i][2]])

    with open(actual_dir + "/" + jsonName, 'w', encoding='utf-8') as jsonf:  # crétaion JSON
        jsonArray = []
        if nb_update != 0:
            for i in range(nb_update):
                name = update[i][0].split('/')[len(update[i][0].split('/')) - 2]
                jsonArray.append({"Path": update[i][0], "Change type": update[i][1], "Old Value": [name, update[i][2]],
                                  "New Value": [name, update[i][3]]})

        if nb_added != 0:
            for i in range(nb_added):
                jsonArray.append({"ID": add[i][0], "Change type": add[i][1], "New Value": add[i][2]})

        if nb_remove != 0:
            for i in range(nb_remove):
                jsonArray.append({"ID": remove[i][0], "Change type": remove[i][1], "Old Value": remove[i][2]})

        jsonString = json.dumps(jsonArray, indent=4)
        jsonf.write(jsonString)

    return nb_update, nb_added, nb_remove


def cleanDirectory(directory):  # Nettoie les dossiers
    if os.path.exists(directory):
        for root, dirs, files in os.walk(directory):
            for d in dirs:
                os.chmod(path.join(root, d), stat.S_IRWXU)
            for file in files:
                os.chmod(path.join(root, file), stat.S_IRWXU)
        shutil.rmtree(directory)


def getId(old_d):
    id = ""
    for object in old_d:
        keys = list(object.keys())
        for i in range(len(keys) - 1):
            if 'id' in keys[i] or 'Id' in keys[i]:
                return keys[i]
    return id


def delta(old_dir, new_dir, actual_dir):
    json_reports = []
    for filename in os.listdir(old_dir):
        old_file = os.path.join(old_dir, filename)
        new_file = os.path.join(new_dir, filename)

        if os.stat(old_file).st_size == 0 or os.stat(new_file).st_size == 0:  # Si on a une dossier vide
            if len(old_file) > len(new_file):
                nbObject = len(old_file)
                json_reports.append(
                    {'File Name': filename, 'Change type': "Suppression", 'Number of lines concerned': str(nbObject)})

            elif len(old_file) < len(new_file):
                nbObject = len(new_file)
                json_reports.append(
                    {'File Name': filename, 'Change type': "Addition", 'Number of lines concerned': str(nbObject)})

        else:  # si les deux dossiers on des données

            with open(old_file) as json1:
                old_data = json.load(json1)
            with open(new_file) as json2:
                new_data = json.load(json2)

            csvName = getFilename(filename) + '.csv'
            jsonName = getFilename(filename) + '.json'
            if DeepDiff(old_data, new_data) != {}:  # si différence entre les 2 fichiers JSON
                id = getId(old_data)  # recup de l'id de l'object
                list_old_id, list_new_id = {}, {}

                for data in old_data:
                    old_id = data[id]
                    list_old_id[old_id] = data
                for d in new_data:
                    new_id = d[id]
                    list_new_id[new_id] = d
                updated, removed, added = {}, {}, {}

                for k in list(list_old_id.keys()):  # trie les data si il y a eu update ou removed ou added
                    if k in list_new_id:
                        if DeepDiff(list_old_id[k], list_new_id[k]) != {}:
                            updated[k] = DeepDiff(list_old_id[k], list_new_id[k])
                        list_new_id.pop(k)
                        list_old_id.pop(k)

                removed = list_old_id
                added = list_new_id

                nbLigne, nbObjectAdded, nbObjectRemoved = getInfo(updated, removed, added, csvName, actual_dir,
                                                                  jsonName, id)

                json_reports.append({'File Name': filename, 'Update': nbLigne, 'Addition': nbObjectAdded,
                                     'Suppresion': nbObjectRemoved})

    with open(actual_dir + REPORT, 'w') as outfile:
        json.dump(json_reports, outfile, indent=4)


def lambda_handler(event, context):
    message = json.loads(event.get("body"))
    github_org, github_repo = message.get("github_org"), message.get("github_repo")

    current_backup = Backupta(github_org, github_repo, workspace=DEFAULT_WORKSPACE + "/current")
    old_backup = Backupta(github_org, github_repo, workspace=DEFAULT_WORKSPACE + "/old")
    new_backup = Backupta(github_org, github_repo, workspace=DEFAULT_WORKSPACE + "/new")

    current_backup.clone_repo()
    old_backup.clone_repo()
    new_backup.clone_repo()

    if message.get('github_branch') is not None:
        current_backup.checkout_branch(message.get('github_branch'))
        old_backup.checkout_branch(message.get('github_branch'))
        new_backup.checkout_branch(message.get('github_branch'))

    # Chemin pour stocker les données
    new_dir = new_backup.workspace
    old_dir = old_backup.workspace
    actual_dir = current_backup.workspace

    # Recuperation des 2 derniers commit
    commits = list(old_backup.repo.iter_commits(message.get('github_branch'), max_count=2))

    if message.get('new_commit') in [None, ""]:
        new_commit = commits[0]
    else:
        new_commit = message.get('new_commit')

    if message.get('old_commit') in [None, ""]:
        old_commit = commits[1]
    else:
        old_commit = message.get('old_commit')

    # Checkout sur les commits indiqués
    new_backup.checkout_branch(new_commit)
    old_backup.checkout_branch(old_commit)

    # FAIRE LA COMPARAISON

    # Chemin des dossiers où sont stockées les informations
    new_dir = new_dir + jsonFromTalend
    old_dir = old_dir + jsonFromTalend

    iso_date = datetime.datetime.now().isoformat()

    if not os.path.exists(actual_dir + backup):
        os.makedirs(actual_dir + backup)

    actual_dir = actual_dir + backup + "/" + iso_date
    os.makedirs(actual_dir)

    delta(old_dir, new_dir, actual_dir)
    current_backup.set_git_author('Delta Inspector', 'inspector@lambda.com')
    current_backup.save(f"Added backup report {iso_date}")

    return {
        'statusCode': 200,
        'body': json.dumps('Hello form lambda')
    }


if __name__ == '__main__':
    message = {
        'github_org': 'Azmah-Bad',
        'github_repo': 'backup-test',
        'github_branch': 'dev',
        'old_commit': '',
        'new_commit': '',
        'token': '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',
        'username': 'NinaNedjar'
    }
    event = {
        "body": json.dumps(message)
    }
    lambda_handler(event, None)

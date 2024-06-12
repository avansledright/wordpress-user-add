import mysql.connector
from mysql.connector import errorcode
import random
import string
import sys
import re

def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(length))
    return password
def get_db_config(domain_name):
    config_path = f"/var/www/{domain_name}/wp-config.php"

    db_config = {
        "DB_NAME": None,
        "DB_USER": None,
        "DB_PASSWORD": None,
        "DB_HOST": None
    }

    try:
        with open(config_path, 'r') as file:
            for line in file:
                if re.match(r"define\('DB_NAME',", line):
                    db_config["DB_NAME"] = re.search(r"define\('DB_NAME',\s*'(.+?)'\);", line).group(1)
                elif re.match(r"define\('DB_USER',", line):
                    db_config["DB_USER"] = re.search(r"define\('DB_USER',\s*'(.+?)'\);", line).group(1)
                elif re.match(r"define\('DB_PASSWORD',", line):
                    db_config["DB_PASSWORD"] = re.search(r"define\('DB_PASSWORD',\s*'(.+?)'\);", line).group(1)
                elif re.match(r"define\('DB_HOST',", line):
                    db_config["DB_HOST"] = re.search(r"define\('DB_HOST',\s*'(.+?)'\);", line).group(1)
                elif re.match(r"\$table_prefix\s*=", line):
                    db_config["TABLE_PREFIX"] = re.search(r"\$table_prefix\s*=\s*'(.+?)';", line).group(1)

    except FileNotFoundError:
        print(f"wp-config.php not found for {domain_name}")
        return None

    return db_config
def add_admin_user(state_name):
    db_config = get_db_config(state_name)
    if not db_config:
        return
    domain_name = f"greenway{state_name}.com"
    user_login = f"{state_name}_admin"
    user_email = sys.argv[2]
    user_pass = generate_random_password()

    try:
        cnx = mysql.connector.connect(user=db_config['DB_USER'], password=db_config['DB_PASSWORD'], host=db_config['DB_HOST'], database=db_config['DB_NAME'])
        cursor = cnx.cursor()

        table_prefix = db_config['TABLE_PREFIX']

        add_user = (f"INSERT INTO {table_prefix}users "
                    "(user_login, user_pass, user_nicename, user_email, user_status) "
                    "VALUES (%s, MD5(%s), %s, %s, 0)")
        user_data = (user_login, user_pass, user_login, user_email)

        cursor.execute(add_user, user_data)
        user_id = cursor.lastrowid

        add_usermeta1 = (f"INSERT INTO {table_prefix}usermeta "
                         "(user_id, meta_key, meta_value) "
                         "VALUES (%s, %s, %s)")
        usermeta_data1 = (user_id, f'{table_prefix}capabilities', 'a:1:{s:13:"administrator";s:1:"1";}')

        add_usermeta2 = (f"INSERT INTO {table_prefix}usermeta "
                         "(user_id, meta_key, meta_value) "
                         "VALUES (%s, %s, %s)")
        usermeta_data2 = (user_id, f'{table_prefix}user_level', '10')

        cursor.execute(add_usermeta1, usermeta_data1)
        cursor.execute(add_usermeta2, usermeta_data2)

        cnx.commit()

        cursor.close()
        cnx.close()

        print(f"User created successfully!")
        print(f"Username: {user_login}")
        print(f"Password: {user_pass}")
        print(f"Website URL: https://{domain_name}")
        print(f"Email: {user_email}")

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        cnx.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python add_wp_admin.py <domain_name> <email>")
        sys.exit(1)

    state_name = sys.argv[1]
    add_admin_user(state_name)

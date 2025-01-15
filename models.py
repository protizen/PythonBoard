import mysql.connector
from datetime import datetime

class PostManager:
    def __init__(self):
        self.connection = None
        self.cursor = None
    ## 추후 SQL 암호화 저장 및 비교 구문
    # INSERT INTO members (uid,uname,`password`) VALUES ('kim','김구',PASSWORD('1234'))
    # SELECT * FROM members WHERE uid='kim' AND `password` = PASSWORD('1234')
    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host="localhost",
                user="sejong",
                password="1234",
                database="board_db2"
            )
            self.cursor = self.connection.cursor(dictionary=True)
            self.cursor.execute("""
                                CREATE TABLE IF NOT EXISTS `posts` (
                                `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
                                `title` varchar(200) NOT NULL,
                                `content` text NOT NULL,
                                `filename` varchar(255) DEFAULT NULL,
                                `write_id` varchar(50) DEFAULT NULL,
                                `created_at` datetime NOT NULL DEFAULT current_timestamp(),
                                `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
                                `views` int(11) DEFAULT 0,
                                PRIMARY KEY (`id`)
                                )
                                """)
            self.cursor.execute("""
                                CREATE TABLE IF NOT EXISTS `members` (
                                `idx` int(10) unsigned NOT NULL AUTO_INCREMENT,
                                `uid` varchar(50) DEFAULT NULL,
                                `uname` varchar(50) DEFAULT NULL,
                                `password` varchar(50) DEFAULT NULL,
                                `age` tinyint(4) DEFAULT NULL,
                                `email` varchar(100) DEFAULT NULL,
                                `regdate` datetime DEFAULT current_timestamp(),
                                PRIMARY KEY (`idx`)
                                )
                                """)
        except mysql.connector.Error as error:
            print(f"데이터베이스 연결 실패: {error}")

    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()

    def get_all_posts(self, page=1, per_page=10):
        try:
            self.connect()
            offset = (page - 1) * per_page
            self.cursor.execute("SELECT COUNT(*) as total FROM posts")
            total = self.cursor.fetchone()['total']

            sql = """
                SELECT a.*, b.uname FROM posts a 
                LEFT JOIN members b ON a.write_id = b.uid  
                ORDER BY a.created_at DESC 
                LIMIT %s, %s
            """
            self.cursor.execute(sql, (offset, per_page))
            posts = self.cursor.fetchall()

            total_pages = (total + per_page - 1) // per_page
            return posts, total_pages
        except mysql.connector.Error as error:
            print(f"게시글 조회 실패: {error}")
            return [], 0
        finally:
            self.disconnect()

    def insert_post(self, title, content, filename, writer):
        try:
            self.connect()
            sql = """
                INSERT INTO posts 
                (title, content, filename, created_at, write_id, views) 
                VALUES (%s, %s, %s, %s, %s, 0)
            """
            values = (title, content, filename, datetime.now(), writer)
            self.cursor.execute(sql, values)
            self.connection.commit()
            return True
        except mysql.connector.Error as error:
            self.connection.rollback()
            print(f"게시글 추가 실패: {error}")
            return False
        finally:
            self.disconnect()

    def get_post_by_id(self, id):
        try:
            self.connect()

            self.cursor.execute(
                "UPDATE posts SET views = views + 1 WHERE id = %s",
                (id,)
            )
            self.connection.commit()

            sql = """SELECT a.*, b.uname FROM posts a
                    LEFT JOIN members b ON a.write_id = b.uid 
                    WHERE a.id = %s"""
            self.cursor.execute(sql, (id,))
            return self.cursor.fetchone()
        except mysql.connector.Error as error:
            print(f"게시글 조회 실패: {error}")
            return None
        finally:
            self.disconnect()

    def update_post(self, id, title, content, filename):
        try:
            self.connect()
            sql = """
                UPDATE posts 
                SET title = %s, content = %s, filename = %s 
                WHERE id = %s
            """
            values = (title, content, filename, id)
            self.cursor.execute(sql, values)
            self.connection.commit()
            return True
        except mysql.connector.Error as error:
            self.connection.rollback()
            print(f"게시글 수정 실패: {error}")
            return False
        finally:
            self.disconnect()

    def delete_post(self, id):
        try:
            self.connect()
            
            self.cursor.execute("SELECT filename FROM posts WHERE id = %s", (id,))
            result = self.cursor.fetchone()

            sql = "DELETE FROM posts WHERE id = %s"
            self.cursor.execute(sql, (id,))
            self.connection.commit()

            return True, result['filename'] if result else None
        except mysql.connector.Error as error:
            self.connection.rollback()
            print(f"게시글 삭제 실패: {error}")
            return False, None
        finally:
            self.disconnect()

    def login_check(self, userid, password):
        try:
            self.connect()
            sql = "SELECT * FROM members WHERE uid = %s and password = %s"
            self.cursor.execute(sql, (userid, password))
            result = self.cursor.fetchone()
            if result:
                return True, result.get('uname','무명')
            return False, ''
        except mysql.connector.Error as error:
            self.connection.rollback()
            print(f"로그인 실패: {error}")
            return None
        finally:
            self.disconnect()

    def duplicate_member(self, userid):
        try:
            self.connect()
            sql = "SELECT * FROM members WHERE uid = %s"
            self.cursor.execute(sql, (userid,))
            result = self.cursor.fetchone()
            if result:
                return True
            return False
        except mysql.connector.Error as error:
            self.connection.rollback()
            print(f"확인 실패: {error}")
            return None
        finally:
            self.disconnect()

    def register_member(self, userid, username, password):
        try:
            self.connect()
            sql = """
                INSERT INTO members
                (uid, uname, password) VALUES
                (%s,%s,%s)  
            """
            values = (userid, username, password)
            self.cursor.execute(sql, values)
            self.connection.commit()
            return True
        except mysql.connector.Error as error:
            self.connection.rollback()
            print(f"회원가입 실패: {error}")
            return False
        finally:
            self.disconnect()
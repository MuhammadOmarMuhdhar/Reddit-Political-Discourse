import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import pandas as pd
import sqlite3
from sqlalchemy import create_engine
import random


def reddit_scrape(subreddit):
    base_url = f'https://old.reddit.com/r/{subreddit}/top/?sort=top&t=week'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    all_posts = []
    next_button = ''
    pages = 10



    for i in range(pages):
        url = base_url if next_button == '' else next_button
        response = requests.get(url, headers=headers)

        
        if response.status_code == 200:

            soup = BeautifulSoup(response.content, 'html.parser')
            posts = soup.find_all(class_='thing')

            for post in posts:
                date_element = post.find('time')
                if date_element:
                    post_date_str = date_element['datetime']
                    post_date = datetime.strptime(post_date_str[:10], '%Y-%m-%d')
                    formatted_date = post_date.strftime('%Y-%m-%d')
                    
                    # Append post information
                    post_info = {
                        'post_data': post,
                        'date': formatted_date
                    }
                    all_posts.append(post_info)
                    
                    # Check if the post date is on or before the stop date
                    # if post_date <= stop_date:
                    #     break

            # If the loop was broken (i.e., stop date reached), exit the outer loop
            # if post_date <= stop_date:
            #     break
            
            # Find the next button link to go to the next page
            next_button_find = soup.find('span', class_='next-button')
            if next_button_find:
                next_button = next_button_find.find('a')['href']
            else:
                break

        # Error handling
        else:
            print(f"Failed to retrieve page. Status code: {response.status_code}")
            break

        time.sleep(6)
    
    links = []
    for post in all_posts:
        date = post.get('date')[:10]
        post_info = post.get('post_data')
        url = post_info.get('data-permalink')
        link_url = f'https://old.reddit.com/{url}.json'
        post_info = {
            'link': link_url,
            'date': date
        }
        links.append(post_info)

    comments = []

    def extract_body(data):
        if isinstance(data, dict):
            if 'body' in data:
                comment_info = {
                    'body': data['body'],
                    'date': date
                }
                comments.append(comment_info)
            for key, value in data.items():
                extract_body(value)
        elif isinstance(data, list):
            for item in data:
                extract_body(item)

    for link in links: 
        date = link.get('date')
        json_url = link.get('link')

        response = requests.get(json_url, headers=headers)
        # comment_data = []

        # 5.error handling 
        
        if response.status_code == 200:
            data = response.json()
            extract_body(data)
        else: 
            print(f"Failed to retrieve page. Status code: {response.status_code}")
            print(json_url)

       
        time.sleep(6)

    df = pd.DataFrame(comments)

    db_file_path = '/Users/muhammadmuhdhar/Desktop/Repo/Reddit Politics/data.db'
    # connection = sqlite3.connect(db_file_path)
    engine = create_engine(f'sqlite:///{db_file_path}')
    df.to_sql(subreddit, con=engine, if_exists='append', index=False)

    engine.dispose()

        




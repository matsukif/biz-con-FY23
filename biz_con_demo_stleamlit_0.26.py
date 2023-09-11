import streamlit as st
import openai
from bs4 import BeautifulSoup
import html
import re
import requests
import json


def main():
    st.set_page_config(
        initial_sidebar_state="expanded",
        page_title="BabyAGI Streamlit",
        layout="centered",
    )

#     text_splitter = RecursiveCharacterTextSplitter(
#       chunk_size = 2000,
#       chunk_overlap = 100,
#       length_function = len,
#     )

    system_prompt3 = """
    このスレッドでは以下ルールを厳格に守ってください。
    あなたはニュース記事から悪事を働いた会社の名前を抽出して回答するシステムです。
    ・悪事を働いた会社の会社名を抽出します。
    ・以下の会社名は抽出しないでください。
     ・悪事を働いた会社から被害をうけた会社
     ・悪事に加担していない会社
     ・悪事に関係ない会社
     ・悪事を働いた会社と関係を切ろうとしている会社
    ・悪事を働いたか判断が難しい場合は、会社名を抽出し、会社名の最後に"（悪事を働いた可能性あり）"を追加してください。
    ・記事には本文の他にアクセスランキングや広告がありますが、本文からのみ会社名を抽出してください。
    ・会社名が20社以上の場合は20社目まで出力してください。
    ・会社ごと、どのような悪事を働いたか40文字程度で記載してください。
    ・応答はjsonとしてください。"companies"というキーの配下に会社名は"name"、悪いことの内容は"problem"をキーを設定してください。
    ・jsonのフォーマットは以下です。
        {
            "companies": [
            {
                "name": "ソフトバンクグループ",
                "problem": "インサイダーとひり引きを実施した"
            },
            {
                "name": "アーム",
                "problem": "談合を主導した"
            },
            {
                "name": "磯丸水産",
                "problem": "（悪事をは働いた可能性あり）談合に参加した"
            }
            ]
        }
    """    
    with st.sidebar:
#        openai_api_key = st.text_input('Your OpenAI API KEY', type="password")
        model_name = st.selectbox("Model name", options=["gpt-3.5-turbo-0613", "gpt-4"])
        temperature = st.slider(
            label="Temperature",
            min_value=0.0,
            max_value=2.0,
            step=0.1,
            value=0.0,
        )
        system_prompt3_input = st.text_area("「３．悪事を働いた会社」のプロンプト",value=system_prompt3)


    st.title("法人不芳情報抽出 ver0.2")
#    target_company = st.text_input("調査したい企業名を入力してください")
    url = st.text_input("調査したい記事のURLを入力してください")
    if url:

        response = requests.get(url)
        site_data = response.text

        soup = BeautifulSoup(site_data, 'html.parser')

        # bodyタグの中を対象とする
        body_content = soup.body

        # 本文を含むすべての<p>タグを抽出
        paragraphs = body_content.find_all('p')

        # 文章のテキスト部分を取得
#        article_texts = [p.get_text() for p in paragraphs if "有料会員になると" not in p.get_text()]
        article_texts = [p.get_text() for p in paragraphs]

        # テキスト部分を結合して表示
        article_content = "\n".join(article_texts)

#    max_iterations = st.number_input("Max iterations", value=3, min_value=1, step=1)
    button = st.button("開始")

    if button:
        try:
#            openai.api_key = openai_api_key
            openai.api_key = st.secrets.OpenAIAPI.openai_api_key

#記事要約
            system_prompt1 = """
            このスレッドでは以下ルールを厳格に守ってください。
            あなたはニュース記事を要約するシステムです。
            ・記事には本文の他にアクセスランキングや広告があります。本文のみ要約してください。
            ・150文字程度に要約してください。
            ・１行目はタイトルを記載してください。２行目から要約を記載してください。
            """

            response1 = openai.ChatCompletion.create(
                model = model_name,
                temperature = temperature,
                messages=[
                    {"role":"system", "content": system_prompt1},
                    {"role":"user", "content": article_content}
                ]
            )

            article_summary = response1["choices"][0]["message"]["content"]
            st.write("１．記事要約")            
            st.write(article_summary)


#会社名の抽出（ターゲット会社との関係性付き）
            system_prompt2 = """
            このスレッドでは以下ルールを厳格に守ってください。
            あなたはニュース記事から全ての会社名を抽出して回答するシステムです。
            ・記事には本文の他にアクセスランキングや広告がありますが、本文からのみ会社名を抽出してください。
            ・会社名が20社以上の場合は20社目まで出力してください。
            ・会社ごと位置づけを簡潔に30文字程度で記載してください。
            ・応答はjsonとしてください。"companies"というキーの配下に会社名は"name"、位置づけは"position"を設定してください。
            ・jsonのフォーマットは以下です。
                {
                    "companies": [
                    {
                        "name": "ソフトバンクグループ",
                        "position": "孫正義会長兼社長"
                    },
                    {
                        "name": "アーム",
                        "position": "英半導体設計大手"
                    },
                    {
                        "name": "磯丸水産",
                        "position": "飲食チェーン"
                    }
                    ]
                }
            """

            response2 = openai.ChatCompletion.create(
#                model="gpt-3.5-turbo",
                model = model_name,
                temperature = temperature,
                messages=[
                    {"role":"system", "content": system_prompt2},
                    {"role":"user", "content": article_content}
                ]
            )

#            company_name = response["choices"][0]["message"]
            company_name_str = {}
            company_name_str = response2["choices"][0]["message"]["content"]
            company_name_json = json.loads(company_name_str)

            st.write("========================================================================================")
            st.write("２．記事にある会社（最大20社）")

            number = 1
            company_list = []

            for item in company_name_json["companies"]:
                st.write(f"({number}) {item['name']} ： {item['position']}")
                company_list.append(item['name'])
                number += 1


#会社名の抽出２（悪いことを行った会社の抽出）
#system_pronpt3は上のほうへ移植

            response2 = openai.ChatCompletion.create(
#                model="gpt-3.5-turbo",
                model = model_name,
                temperature = temperature,
                messages=[
                    {"role":"system", "content": system_prompt3_input},
                    {"role":"user", "content": article_content}
                ]
            )

#            company_name = response["choices"][0]["message"]
            company_name_str2 = {}
            company_name_str2 = response2["choices"][0]["message"]["content"]
            company_name_json2 = json.loads(company_name_str2)

            st.write("========================================================================================")
            st.write("３．悪事を働いた会社（最大20社）")

            number = 1
#            company_list = []

            for item in company_name_json2["companies"]:
                st.write(f"({number}) {item['name']} ： {item['problem']}")
#                company_list.append(item['name'])
                number += 1


#Wikipediaの情報収集
            def get_wikipedia_etxract(title):
                WIKIPEDIA_ENDPOINT = "https://ja.wikipedia.org/w/api.php"

                parameters = {
                    "action": "query",
                    "format": "json",
                    "titles": title,
                    "prop": "extracts",  # ページの内容を取得
                    "exintro": True,  # イントロのみ取得（冒頭部分）
                }

                response = requests.get(WIKIPEDIA_ENDPOINT, params=parameters)
                data = response.json()

                # ページの内容を取得
                pages = data["query"]["pages"]
                for pageid, page in pages.items():
#                    html_content = page["extract"]  # イントロの内容を返す
                    if "extract" in page:
                        html_content = page["extract"]  # イントロの内容を返す
                        #HTMLタグを削除
                        text_content = re.sub(r'<.*?>', '', html_content)
                        
                        # HTMLエンティティをデコード（例: &amp; を & に変換）
                        decoded_content = html.unescape(text_content)
                    else:
                        decoded_content = ""

                return decoded_content

            def get_wikipedia_sections(title):
                WIKIPEDIA_ENDPOINT = "https://ja.wikipedia.org/w/api.php"

                parameters = {
                    "action": "parse",
                    "format": "json",
                    "page": title,
                    "prop": "sections",
                }

                response = requests.get(WIKIPEDIA_ENDPOINT, params=parameters)
                data = response.json()

                return data["parse"]["sections"]

            def get_section_content(title, section_id):
                WIKIPEDIA_ENDPOINT = "https://ja.wikipedia.org/w/api.php"

                parameters = {
                    "action": "parse",
                    "format": "json",
                    "page": title,
                    "section": section_id,
                    "prop": "text",
                }

                response = requests.get(WIKIPEDIA_ENDPOINT, params=parameters)
                data = response.json()

                html_content = data["parse"]["text"]["*"]

                # HTMLタグを取り除く
                soup = BeautifulSoup(html_content, 'html.parser')
                return soup.get_text()

            st.write("")
            st.write("========================================================================================")
#            st.write("４．Wikipedia検索結果（対象：悪事を働いた会社）")
            st.write("４．Wikipedia検索結果")

            for item in company_list:
                title = item
                extract_content = get_wikipedia_etxract(title)
                if not extract_content:
                    continue
                sections = get_wikipedia_sections(title)
                summary_content = ""
                incident_content = ""

                for section in sections:
                    if '概要' in section['line']:
                        summary_content = get_section_content(title, section['index'])
                    if '不祥事' in section['line']:
                        incident_content = get_section_content(title, section['index'])

                st.write(item)
                st.write(extract_content)
                st.write("< 概要 >")
                st.write(summary_content)

                st.write("< 不祥事 >")
                st.write(incident_content)
                st.write("-------------------------------------------------------------")



        except Exception as e:
            st.error(e)

if __name__ == "__main__":
    main()

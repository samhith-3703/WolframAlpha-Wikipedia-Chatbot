import streamlit as st
import wolframalpha
import wikipedia
import requests
import os
from difflib import SequenceMatcher
from dotenv import load_dotenv
load_dotenv()

# Set Streamlit page configuration
st.set_page_config(page_title="QT Bot", page_icon="🎀", layout="wide")

# Wolfram Alpha API Client
appId = os.getenv('WOLFRAM_APP_ID')
client = wolframalpha.Client(appId)

def is_relevant_page(title, keyword):
    # Check if the page title is closely related to the keyword
    return SequenceMatcher(None, title.lower(), keyword.lower()).ratio() > 0.6

def search_wiki(keyword=''):
    # Running the query
    search_results = wikipedia.search(keyword)
    if not search_results:
        st.write("No result from Wikipedia")
        return None, None
    
    for result in search_results:
        try:
            page = wikipedia.page(result)
            # Check if the page title or summary matches the keyword closely
            if is_relevant_page(page.title, keyword) or is_relevant_page(page.summary[:200], keyword):
                wiki_summary = str(page.summary)
                image_url = primary_image(page.title)
                return wiki_summary, image_url
        except wikipedia.DisambiguationError as err:
            for option in err.options:
                try:
                    page = wikipedia.page(option)
                    # Apply the same relevance check for disambiguation options
                    if is_relevant_page(page.title, keyword) or is_relevant_page(page.summary[:200], keyword):
                        wiki_summary = str(page.summary)
                        image_url = primary_image(page.title)
                        return wiki_summary, image_url
                except wikipedia.PageError:
                    continue
        except wikipedia.PageError:
            continue
        except Exception as err:
            st.write("An error occurred while searching Wikipedia:", err)
            return None, None

    # If no relevant page found
    st.write("No relevant information found on Wikipedia.")
    return None, None
def search(text=''):
    try:
        res = client.query(text)
        # Check if the response contains pods
        if not res.get('pod'):
            st.write('Wolfram Alpha could not provide a specific answer, trying Wikipedia...')
            wiki_summary, image_url = search_wiki(text)
            if wiki_summary:
                st.write(wiki_summary)
                if image_url:
                    st.image(image_url, caption="Wikipedia Image")
            else:
                st.write("No relevant information found in Wikipedia.")
            return

        result = ''
        # pod[0] is the question
        pod0 = res['pod'][0]
        # pod[1] may contain the answer
        pod1 = res['pod'][1] if len(res['pod']) > 1 else None
        # checking if pod1 has primary=true or title=result|definition
        if pod1 and (('definition' in pod1['@title'].lower()) or ('result' in pod1['@title'].lower()) or (pod1.get('@primary', 'false') == 'true')):
            # extracting result from pod1
            result = resolve_list_or_dict(pod1['subpod'])
            st.success(result)
        else:
            # extracting Wolfram question interpretation from pod0
            question = resolve_list_or_dict(pod0['subpod'])
            # searching for response from Wikipedia
            st.write('Wolfram Alpha could not provide a specific answer, trying Wikipedia...')
            wiki_summary, image_url = search_wiki(question)
            if wiki_summary:
                st.write(wiki_summary)
                if image_url:
                    st.image(image_url, caption="Wikipedia Image")
            else:
                st.write("No relevant information found in Wikipedia.")
    except Exception as e:
        st.write("An error occurred while searching:", str(e))
def resolve_list_or_dict(variable):
    if isinstance(variable, list):
        return variable[0].get('plaintext', '')
    else:
        return variable.get('plaintext', '')

def primary_image(title=''):
    url = 'http://en.wikipedia.org/w/api.php'
    data = {
        'action': 'query',
        'prop': 'pageimages',
        'format': 'json',
        'piprop': 'original',
        'titles': title
    }
    try:
        res = requests.get(url, params=data)
        key = list(res.json()['query']['pages'].keys())[0]
        image_url = res.json()['query']['pages'][key].get('original', {}).get('source', None)
        return image_url
    except Exception as err:
        st.write('Exception while finding image:', str(err))
        return None

# Custom CSS to adjust the interface width
st.markdown(
    """
    <style>
    .main {
        max-width: 800px;
        margin: 0 auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Streamlit User Interface
st.title("Ask Questions to Simple QBot")
# Main chat interface
st.markdown("<hr style='border:1px solid gray'>", unsafe_allow_html=True)
user_input = st.text_input("Ask me a question:", "")

if user_input:
    with st.spinner("Searching for the answer..."):
        search(user_input)

# Footer section
st.markdown("<hr style='border:1px solid gray'>", unsafe_allow_html=True)

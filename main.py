import streamlit as st
from few_shot import FewShotPosts
from post_generator import generate_post


def main():
    st.title("LinkedIn post Generator")
    col1, col2, col3 = st.columns(3)
    fs = FewShotPosts()

    length_options = ["Short", "Medium", "Long"]
    language_options = ["English", "Hinglish"]

    with col1:
        selected_tag = st.selectbox("Title", options=fs.get_tags())

    with col2:
        selected_length = st.selectbox("Length", options=length_options)

    with col3:
        selected_language = st.selectbox("Language", options=language_options)

    if st.button("Generate"):
        # Assign the returned value to 'post'
        post = generate_post(selected_length, selected_language, selected_tag)
        st.write(post)


if __name__ == "__main__":
    main()
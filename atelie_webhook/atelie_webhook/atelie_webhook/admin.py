import streamlit as st
import models
from database import SessionLocal
import os
from dotenv import load_dotenv

load_dotenv()

# ------------------ AUTH ------------------
def check_password():
    if "auth" not in st.session_state:
        st.session_state.auth = False

    if not st.session_state.auth:
        user = st.sidebar.text_input("Usuário")
        pw = st.sidebar.text_input("Senha", type="password")

        if st.sidebar.button("Login"):
            if user == os.getenv("ADMIN_USER") and pw == os.getenv("ADMIN_PW"):
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Credenciais inválidas")

        return False

    return True


# ------------------ APP ------------------
if check_password():
    st.title("🧶 Painel de Administração")

    db = SessionLocal()

    # controle de edição
    if "editando_id" not in st.session_state:
        st.session_state.editando_id = None

    menu = st.sidebar.selectbox("Ação", ["Produtos", "Adicionar Produto"])

    # ------------------ ADD ------------------
    if menu == "Adicionar Produto":
        with st.form("cadastro"):
            nome = st.text_input("Nome")
            preco = st.number_input("Preço", min_value=0.0)
            estoque = st.number_input("Estoque", min_value=0)
            img = st.text_input("URL da Imagem")
            cat = st.selectbox("Categoria", ["Tapete", "Jogo de mesa", "Bolsa"])
            desc = st.text_area("Descrição")

            if st.form_submit_button("Salvar"):
                p = models.Produto(
                    nome=nome,
                    preco=preco,
                    estoque=estoque,
                    imagem_url=img,
                    categoria=cat,
                    descricao=desc
                )
                db.add(p)
                db.commit()
                st.success("Produto cadastrado!")
                st.rerun()

    # ------------------ LISTAGEM ------------------
    else:
        produtos = db.query(models.Produto).all()

        for p in produtos:
            col1, col2 = st.columns([1, 4])

            with col1:
                if p.imagem_url and p.imagem_url.strip():
                    st.image(p.imagem_url)
                else:
                    st.warning("Sem foto")

            with col2:
                st.write(f"**{p.nome}** - R$ {p.preco} (Estoque: {p.estoque})")

                col_btn1, col_btn2 = st.columns(2)

                # EXCLUIR
                with col_btn1:
                    if st.button("Excluir", key=f"del_{p.id}"):
                        db.delete(p)
                        db.commit()
                        st.rerun()

                # EDITAR
                with col_btn2:
                    if st.button("Editar", key=f"edit_{p.id}"):
                        st.session_state.editando_id = p.id
                        st.rerun()

                # FORM DE EDIÇÃO
                if st.session_state.editando_id == p.id:
                    st.markdown("---")
                    st.subheader(f"Editando: {p.nome}")

                    with st.form(f"edit_form_{p.id}"):
                        nome = st.text_input("Nome", value=p.nome)
                        preco = st.number_input("Preço", min_value=0.0, value=float(p.preco))
                        estoque = st.number_input("Estoque", min_value=0, value=int(p.estoque))
                        img = st.text_input("URL da Imagem", value=p.imagem_url or "")
                        categorias = ["Tapete", "Jogo de mesa", "Bolsa"]

                        try:
                            index_cat = categorias.index(p.categoria)
                        except ValueError:
                            index_cat = 0

                        cat = st.selectbox("Categoria", categorias, index=index_cat)
                        desc = st.text_area("Descrição", value=p.descricao or "")

                        col_save, col_cancel = st.columns(2)

                        salvar = col_save.form_submit_button("Salvar")
                        cancelar = col_cancel.form_submit_button("Cancelar")

                        if salvar:
                            p.nome = nome
                            p.preco = preco
                            p.estoque = estoque
                            p.imagem_url = img
                            p.categoria = cat
                            p.descricao = desc

                            db.commit()

                            st.session_state.editando_id = None
                            st.success("Produto atualizado!")
                            st.rerun()

                        if cancelar:
                            st.session_state.editando_id = None
                            st.rerun()
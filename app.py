"""Local review interface with an explicit free-only OpenRouter mode."""

import asyncio

import streamlit as st

from ba_assistant.exports import export_json, export_markdown
from ba_assistant.openrouter import FreeProviderConfig, OpenRouter
from ba_assistant.runtime import refresh_workflow
from ba_assistant.session import Session
from ba_assistant.ui_errors import error_message
from ba_assistant.validation import finalization_errors
from ba_assistant.workflow import Workflow, WorkflowError

st.set_page_config(page_title="Помічник бізнес-аналітика", page_icon="📝")
st.title("Помічник бізнес-аналітика")
st.caption("Опишіть проєкт → перевірте вимоги → отримайте документи.")

# Discard only a retained legacy demo; live sessions keep their data on rerun.
previous = st.session_state.get("workflow")
if previous is not None and type(previous.provider).__module__ == "ba_assistant.demo":
    st.session_state.pop("workflow", None)
if "workflow" not in st.session_state:
    st.session_state.live_mode = False
    st.info("Підключіть OpenRouter, щоб почати роботу.")
    st.caption("Ключ зберігається лише в пам’яті сеансу. Платні моделі вимкнені.")
    st.text_input("Ключ OpenRouter", type="password", key="api_key")

    def connect():
        try:
            config = FreeProviderConfig(api_key=st.session_state.api_key)
        except ValueError:
            st.session_state.error = "Введіть ключ OpenRouter."
            return
        st.session_state.clear()
        st.session_state.workflow = Workflow(Session(), OpenRouter(config))

    st.button("Підключити", key="connect", on_click=connect)
    if "error" in st.session_state:
        st.error(st.session_state.error)
    st.stop()

st.session_state.workflow = refresh_workflow(st.session_state.workflow)
workflow = st.session_state.workflow
session = workflow.session
st.session_state.live_mode = True
st.caption("Підключено безплатну модель · дані надсилаються до OpenRouter")


def action(callback):
    try:
        callback()
    except (ValueError, WorkflowError) as error:
        st.session_state.error = error_message(error)
    else:
        st.session_state.pop("error", None)
    st.rerun()


with st.sidebar:
    with st.expander("Змінити API-ключ"):
        st.caption("Діалог і вимоги збережуться. Новий ключ не скидає ліміти акаунта чи моделі.")
        st.text_input("Новий ключ OpenRouter", type="password", key="replacement_key")

        def replace_key():
            current = st.session_state.workflow
            try:
                values = current.provider.config.model_dump()
                values["api_key"] = st.session_state.replacement_key.strip()
                config = FreeProviderConfig.model_validate(values)
            except ValueError:
                st.session_state.key_notice = "Введіть непорожній ключ. Попередній ключ залишено."
            else:
                current.provider = OpenRouter(config, transport=current.provider.transport,
                                              sleep=current.provider.sleep)
                st.session_state.key_notice = "Ключ замінено. Чинність ще не перевірено; запитів не надіслано."
            finally:
                st.session_state.replacement_key = ""

        st.button("Зберегти новий ключ", key="replace_key", on_click=replace_key)
        if "key_notice" in st.session_state:
            st.caption(st.session_state.key_notice)
    st.caption("Сеанс зберігається в пам’яті. Закриття або перезапуск сервера може його стерти.")
    if st.button("Почати новий сеанс", key="reset"):
        st.session_state.clear()
        st.rerun()
if "error" in st.session_state:
    st.error(st.session_state.error)
state = session.state
if state.pending_analysis:
    st.info("Остання відповідь ще не опрацьована. Попередні дані збережено.")
    if st.button("Повторити аналіз", key="retry", type="primary"):
        action(lambda: asyncio.run(workflow.analyze_pending()))

dialogue, review, documents = st.tabs(["Діалог", "Перевірка", "Документи"])


def render_messages(messages):
    # Group questions from one response; collapse exact repeated user submissions visually.
    groups = []
    for message in messages:
        if groups and groups[-1][0] == message.role:
            if message.text != groups[-1][1][-1]:
                groups[-1][1].append(message.text)
        else:
            groups.append((message.role, [message.text]))
    for role, texts in groups:
        with st.chat_message(role):
            for number, text in enumerate(texts, 1):
                st.text(f"{number}. {text}" if len(texts) > 1 else text)


with dialogue:
    if state.messages:
        last_user = max((i for i, m in enumerate(state.messages) if m.role == "user"), default=0)
        if last_user:
            with st.expander("Попередні повідомлення"):
                render_messages(state.messages[:last_user])
        render_messages(state.messages[last_user:])
    else:
        st.info("Розкажіть, для кого потрібна система і що вона має робити.")
    text = st.chat_input("Ваша відповідь або опис проєкту", max_chars=8000,
                         disabled=state.pending_analysis, key="brief")
    if text:
        with st.spinner("Опрацьовую відповідь…"):
            action(lambda: asyncio.run(workflow.submit(text)))
    if state.facts and not state.pending_analysis:
        st.caption("Перегляньте підсумок на вкладці «Перевірка». Якщо потрібні зміни — напишіть тут.")
        if st.button("Оновити підсумок із діалогу", key="reassess"):
            def reassess():
                session.request_reanalysis()
                asyncio.run(workflow.analyze_pending())
            with st.spinner("Звіряю вимоги з відповідями…"):
                action(reassess)

labels = {"unreviewed": "Очікує перевірки", "confirmed": "Підтверджено",
          "proposed": "Пропозиція", "rejected": "Відхилено", "superseded": "Замінено"}
categories = {"goals": "Мета", "users": "Користувачі", "requirements": "Вимоги",
              "constraints": "Обмеження", "team_roles": "Ролі команди"}
with review:
    if state.facts:
        st.subheader("Що ми погоджуємо")
        for category, title in categories.items():
            facts = [f for f in state.facts if f.category == category
                     and f.status not in {"rejected", "superseded"}]
            if not facts:
                continue
            st.write(f"**{title}**")
            for fact in facts:
                st.text(f"{fact.text} — {labels[fact.status]}")
        with st.expander("Джерела та історія фактів"):
            for fact in state.facts:
                st.text(f"{fact.id} · {labels[fact.status]} · {fact.text}")
                for evidence in fact.evidence:
                    st.text(f"{evidence.message_id}: {evidence.quote}")
        available = {f.id: f for f in state.facts if f.status not in {"rejected", "superseded"}}
        selected = st.multiselect("Оберіть перевірені твердження", list(available),
                                  format_func=lambda fid: available[fid].text,
                                  key=f"review_{state.version}", disabled=state.pending_analysis)
        left, right = st.columns(2)
        if left.button("Підтвердити вибрані", key="confirm", disabled=not selected or state.pending_analysis):
            action(lambda: session.review_facts(selected, confirm=True))
        if right.button("Відхилити вибрані", key="reject", disabled=not selected or state.pending_analysis):
            action(lambda: session.review_facts(selected, confirm=False))
        rejected = {f.id: f for f in state.facts if f.status == "rejected"}
        if rejected:
            st.subheader("Відхилені твердження")
            st.caption("Відхилили помилково? Поверніть твердження до перевірки, а потім підтвердьте його. "
                       "Якщо зміст неправильний — опишіть виправлення в діалозі.")
            restore = st.multiselect("Що повернути до перевірки?", list(rejected),
                                     format_func=lambda fid: categories[rejected[fid].category]
                                     + ": " + rejected[fid].text,
                                     key=f"restore_{state.version}", disabled=state.pending_analysis)
            if st.button("Повернути до перевірки", key="restore_facts",
                         disabled=not restore or state.pending_analysis):
                action(lambda: session.restore_facts(restore))
    else:
        st.info("Після опису проєкту тут з’являться вимоги для перевірки.")


with documents:
    errors = finalization_errors(state)
    if errors:
        if state.pending_analysis:
            st.info("Спочатку завершіть аналіз останньої відповіді.")
        else:
            missing = [title for category, title in categories.items()
                       if not any(f.category == category and f.status == "confirmed" for f in state.facts)]
            if missing:
                st.caption("Ще не підтверджено: " + ", ".join(missing) + ".")
                if any(f.status == "rejected" and categories[f.category] in missing for f in state.facts):
                    st.info("Серед відхилених тверджень є потрібна категорія. На вкладці «Перевірка» "
                            "поверніть її до перегляду або напишіть нове формулювання в «Діалозі».")
            remaining = sum(f.status == "unreviewed" for f in state.facts)
            blockers = sum(i.blocking and not i.resolved for i in state.issues)
            if remaining:
                st.info(f"Тверджень до перегляду на вкладці «Перевірка»: {remaining}.")
            if blockers:
                st.info("Залишилися уточнення. Дайте відповідь асистенту на вкладці «Діалог».")
    if st.button("Створити документи", key="generate", disabled=bool(errors), type="primary"):
        with st.spinner("Готую документи — очікування до 3 хвилин. Вимоги збережено.", show_time=True):
            action(lambda: asyncio.run(workflow.generate()))
    if state.artifacts:
        markdown = export_markdown(state)
        st.markdown(markdown)
        st.download_button("Завантажити Markdown", markdown, "requirements.md", "text/markdown")
        st.download_button("Завантажити JSON", export_json(state),
                           "requirements.json", "application/json")

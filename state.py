def init_session_state(st):
    if "customers" not in st.session_state:
        st.session_state.customers = {}

    if "planned_schedule" not in st.session_state:
        st.session_state.planned_schedule = []

    if "selected_table" not in st.session_state:
        st.session_state.selected_table = "1卓"

    if "manual_assignments" not in st.session_state:
        st.session_state.manual_assignments = {}

    if "actual_assignments" not in st.session_state:
        st.session_state.actual_assignments = {}    
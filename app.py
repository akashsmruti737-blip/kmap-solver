import streamlit as st

# Set up page configurations for an ECE-themed application
st.set_page_config(page_title="ECE Experiential Learning: K-Map Solver", layout="centered")

st.title("🎛️ Karnaugh Map (K-Map) Solver Web Application")
st.subheader("ECE Experiential Learning Task | Digital Electronics")
st.caption("Developed entirely in Python using Streamlit")

# 1. User Interface Controls
num_vars = st.radio(
    "Select Number of Variables:",
    options=[2, 3, 4],
    index=2, # Default to 4 variables
    horizontal=True,
    key="num_vars_radio"
)

# Define physical layouts and Gray code mapping dimensions
map_configs = {
    2: {
        "rows": 2, "cols": 2,
        "row_labels": ['0', '1'], "col_labels": ['0', '1'],
        "row_vars": 'A', "col_vars": 'B',
        "matrix": [[0, 1], [2, 3]]
    },
    3: {
        "rows": 2, "cols": 4,
        "row_labels": ['0', '1'], "col_labels": ['00', '01', '11', '10'],
        "row_vars": 'A', "col_vars": 'BC',
        "matrix": [[0, 1, 3, 2], [4, 5, 7, 6]]
    },
    4: {
        "rows": 4, "cols": 4,
        "row_labels": ['00', '01', '11', '10'], "col_labels": ['00', '01', '11', '10'],
        "row_vars": 'AB', "col_vars": 'CD',
        "matrix": [[0, 1, 3, 2], [4, 5, 7, 6], [12, 13, 15, 14], [8, 9, 11, 10]]
    }
}

config = map_configs[num_vars]
total_cells = 1 << num_vars

# Initialize session state matrix to track cell configurations (0, 1, or X)
if "cell_states" not in st.session_state or len(st.session_state.cell_states) != total_cells:
    st.session_state.cell_states = {i: "0" for i in range(total_cells)}

# Action button to clear the grid
if st.button("🔄 Reset K-Map Grid", type="secondary"):
    st.session_state.cell_states = {i: "0" for i in range(total_cells)}
    st.parent_rerun() if hasattr(st, "parent_rerun") else st.rerun()

st.write("### 🖱️ Click cells to cycle state: `0` ➔ `1` ➔ `X` (Don't Care)")

# 2. Render the Gray-Coded Matrix Grid Using Dynamic Columns
cols = st.columns([1.2] + [1.0] * config["cols"])
cols[0].markdown(f"**{config['row_vars']} \\ {config['col_vars']}**")
for j, label in enumerate(config["col_labels"]):
    cols[j + 1].markdown(f"**{label}**")

# Generate interactive logic blocks row by row
for r in range(config["rows"]):
    cols = st.columns([1.2] + [1.0] * config["cols"])
    cols[0].markdown(f"**{config['row_labels'][r]}**") # Row header label
    
    for c in range(config["cols"]):
        minterm = config["matrix"][r][c]
        current_val = st.session_state.cell_states[minterm]
        
        # Color coding style context based on binary active status
        btn_type = "primary" if current_val == "1" else "secondary"
        btn_label = f"{current_val}\n(m{minterm})"
        
        # Cycle through 0 -> 1 -> X when clicked
        if cols[c + 1].button(btn_label, key=f"cell_{minterm}", use_container_width=True, type=btn_type):
            if current_val == "0":
                st.session_state.cell_states[minterm] = "1"
            elif current_val == "1":
                st.session_state.cell_states[minterm] = "X"
            else:
                st.session_state.cell_states[minterm] = "0"
            st.parent_rerun() if hasattr(st, "parent_rerun") else st.rerun()


# 3. K-Map Matrix Group Simplification Processing Engine
def group_to_expression(group, num_vars):
    vars_list = ['A', 'B', 'C', 'D'][:num_vars]
    common_bits = []
    
    for i in range(num_vars):
        bit_pos = num_vars - 1 - i
        initial_bit = (group[0] >> bit_pos) & 1
        uniform = True
        
        for minterm in group:
            if ((minterm >> bit_pos) & 1) != initial_bit:
                uniform = False
                break
        if uniform:
            common_bits.append(vars_list[i] if initial_bit == 1 else f"{vars_list[i]}'")
            
    return "".join(common_bits) if common_bits else "1"

def solve_kmap():
    states = st.session_state.cell_states
    
    if all(v == "0" for v in states.values()):
        return "0"
    if all(v in ["1", "X"] for v in states.values()):
        return "1"
        
    ones_to_cover = [m for m, v in states.items() if v == "1"]
    if not ones_to_cover:
        return "0"
        
    prime_implicants = []
    max_group_size = total_cells // 2
    
    # Check legal power-of-two loops ([1, 2, 4, 8])
    size = max_group_size
    while size >= 1:
        # FIXED: Loop ranges provided to check all potential sub-box combinations
        for h in [1, 2, 4]:
            for w in [1, 2, 4]:
                if h * w != size or h > config["rows"] or w > config["cols"]:
                    continue
                    
                for r in range(config["rows"]):
                    for c in range(config["cols"]):
                        group = []
                        is_valid = True
                        
                        # Toroidal matrix wrap-around characteristics
                        for gh in range(h):
                            for gw in range(w):
                                nr = (r + gh) % config["rows"]
                                nc = (c + gw) % config["cols"]
                                m = config["matrix"][nr][nc]
                                if states[m] == "0":
                                    is_valid = False
                                    break
                                group.append(m)
                            if not is_valid:
                                break
                                
                        if is_valid:
                            group.sort()
                            if any(m in ones_to_cover for m in group) and group not in prime_implicants:
                                prime_implicants.append(group)
                                ones_to_cover = [m for m in ones_to_cover if m not in group]
        size //= 2

    # Translate identified sets into alphanumeric expressions
    terms = [group_to_expression(g, num_vars) for g in prime_implicants]
    unique_terms = list(dict.fromkeys(terms)) 
    return " + ".join(unique_terms) if unique_terms else "0"

# 4. Display Outputs
minimized_expression = solve_kmap()

st.markdown("---")
st.info(f"### 🖥️ Minimized Algebraic Expression (SOP):\n## **F = {minimized_expression}**")
st.markdown("---")

st.write("#### 📑 Engineering Verification Metrics:")
st.markdown(
    """
    * **Adjacent Term Pairing Strategy:** Resolves grouping logic using a programmatic coordinate scan covering wrap-around margins.
    * **Don't Care Application Optimization:** Yellow cells marked with an **'X'** are adapted by the core loops only if they can drop non-essential literals.
    """
)

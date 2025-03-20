from preswald import connect, get_df, query, table, text, slider, selectbox, alert, checkbox, plotly, card
import plotly.express as px
import pandas as pd
import os
import zipfile

connect()

text("# Big 4 Financial Risk Insights Dashboard (2020-2025) 📊")
text("Interactive analysis of financial risk metrics for the Big 4 accounting firms.")

try:
    df = get_df("/big-4-financial-risk/data/big4_financial_risk_compliance.csv")
    alert("✅ Dataset loaded successfully!")
except:
    try:
        download_path = os.path.expanduser("~/Downloads/big-4-financial-risk-insights-2020-2025.zip")
        
        with zipfile.ZipFile(download_path, 'r') as zip_ref:
            extract_path = os.path.join(os.path.dirname(download_path), "big4_extracted")
            os.makedirs(extract_path, exist_ok=True)
            zip_ref.extractall(extract_path)
        
        csv_files = [f for f in os.listdir(extract_path) if f.endswith('.csv')]
        if csv_files:
            main_file = os.path.join(extract_path, csv_files[0])
            df = pd.read_csv(main_file)
            alert("✅ Dataset loaded from zip file!")
        else:
            alert("⚠️ No CSV files found in the dataset. Please check the dataset structure.")
            df = pd.DataFrame()
    except:
        alert("⚠️ Failed to load dataset. Please check if files exist and are accessible.")
        df = pd.DataFrame()

# Check if dataframe is loaded successfully
if not df.empty:
    # Display dataset overview
    text("## Dataset Overview")
    table(df.head(5), title="Sample Data")
    
    columns = df.columns.tolist()
    
    company_col = next((col for col in columns if "company" in col.lower() or "firm" in col.lower()), columns[0])
    year_col = next((col for col in columns if "year" in col.lower() or "date" in col.lower()), None)
    risk_col = next((col for col in columns if "risk" in col.lower()), None)
    
    text("## Company Filter")
    unique_companies = df[company_col].unique().tolist()
    selected_company = selectbox("Select Company", options=["All"] + unique_companies)
    
    text("## Time Period Selection")
    if year_col:
        unique_years = sorted(df[year_col].unique().tolist())
        start_year = slider("Start Year", min_val=min(unique_years), max_val=max(unique_years), default=min(unique_years))
        end_year = slider("End Year", min_val=min(unique_years), max_val=max(unique_years), default=max(unique_years))
        
        # Filter by year range
        year_filtered_df = df[(df[year_col] >= start_year) & (df[year_col] <= end_year)]
    else:
        year_filtered_df = df
    
    if selected_company != "All":
        filtered_df = year_filtered_df[year_filtered_df[company_col] == selected_company]
    else:
        filtered_df = year_filtered_df
    
    if risk_col:
        text("## Risk Analysis")
        df[risk_col] = pd.to_numeric(df[risk_col], errors='coerce')
        risk_threshold = slider("Risk Threshold", 
                               min_val=filtered_df[risk_col].min(), 
                               max_val=filtered_df[risk_col].max(), 
                               default=filtered_df[risk_col].median())
        
        high_risk_df = filtered_df[filtered_df[risk_col] > risk_threshold]
        table(high_risk_df, title=f"High Risk Entries ({risk_col} > {risk_threshold})")
        
        text("## Risk Trends Over Time")
        if year_col:
            risk_trend = filtered_df.groupby(year_col)[risk_col].mean().reset_index()
            fig = px.line(
                risk_trend,
                x=year_col,
                y=risk_col,
                markers=True,
                title=f'Average {risk_col} Trend ({start_year}-{end_year})',
                labels={risk_col: f'Average {risk_col}', year_col: 'Year'}
            )
            plotly(fig)
    
    # Risk distribution by company visualization
    text("## Risk Distribution by Company")
    if risk_col:
        avg_risk_by_company = filtered_df.groupby(company_col)[risk_col].mean().reset_index().sort_values(by=risk_col, ascending=False)
        fig = px.bar(
            avg_risk_by_company,
            x=company_col,
            y=risk_col,
            title=f"Average {risk_col} by Company",
            labels={risk_col: f'Average {risk_col}', company_col: 'Company'},
            text=risk_col
        )
        fig.update_traces(textposition='outside')
        plotly(fig)
    
    # Financial metrics selection and visualization
    text("## Financial Metrics Analysis")
    numeric_cols = filtered_df.select_dtypes(include=['number']).columns.tolist()
    if risk_col in numeric_cols:
        numeric_cols.remove(risk_col)
    
    if numeric_cols:
        selected_metric = selectbox("Select Financial Metric", options=numeric_cols)
        
        # Generate comparison visualization
        text(f"### {selected_metric} by Company")
        metric_by_company = filtered_df.groupby(company_col)[selected_metric].mean().reset_index().sort_values(by=selected_metric, ascending=False)
        
        fig = px.pie(
            metric_by_company,
            names=company_col,
            values=selected_metric,
            title=f"{selected_metric} Distribution by Company",
            hole=0.3
        )
        plotly(fig)
        
        if year_col:
            text(f"### {selected_metric} Trend Over Time")
            metric_trend = filtered_df.groupby(year_col)[selected_metric].mean().reset_index()
            fig = px.line(
                metric_trend,
                x=year_col,
                y=selected_metric,
                markers=True,
                title=f'Average {selected_metric} Trend ({start_year}-{end_year})',
                labels={selected_metric: f'Average {selected_metric}', year_col: 'Year'}
            )
            plotly(fig)
    
    # SQL Insights using query
    text("## SQL Analysis")
    if company_col and risk_col:
        sql = f"""
        SELECT 
            "{company_col}", 
            AVG("{risk_col}") AS average_risk
        FROM 
            big4_finance
        GROUP BY 
            "{company_col}"
        ORDER BY 
            average_risk DESC
        """
        
        try:
            risk_ranking = query(sql, "big4_finance")
            table(risk_ranking, title="Companies by Average Risk (SQL Analysis)")
        except Exception as e:
            alert(f"⚠️ SQL query failed: {str(e)}")
    
    # Correlation heatmap for numerical columns
    text("## Metric Correlations")
    numeric_cols = filtered_df.select_dtypes(include=['number']).columns
    if len(numeric_cols) > 1:
        correlation_df = filtered_df[numeric_cols].corr()
        fig = px.imshow(
            correlation_df, 
            text_auto=True,
            title="Correlation Heatmap of Financial Metrics",
            color_continuous_scale='RdBu_r'
        )
        plotly(fig)
    
    text("**Financial Wisdom**")
    alert("The Big 4 accounting firms shape the financial landscape of the world's largest companies.")
    checkbox("More analysis options available...")

else:
    text("# ⚠️ No data available")
    text("Please check if the dataset was downloaded correctly and contains data.")
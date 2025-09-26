import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database import get_all_users, get_all_images, get_image_data
from image_processor import convert_image_to_base64
import io
from PIL import Image

def show_admin_dashboard():
    """Display admin dashboard"""
    st.header("🔧 Administrator Dashboard")
    
    # Create tabs for different admin functions
    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "User Management", "Image Analysis", "System Statistics"])
    
    with tab1:
        show_overview_dashboard()
    
    with tab2:
        show_user_management()
    
    with tab3:
        show_image_analysis()
    
    with tab4:
        show_system_statistics()

def show_overview_dashboard():
    """Show overview dashboard with key metrics"""
    st.subheader("System Overview")
    
    # Get data
    users = get_all_users()
    images = get_all_images()
    
    # Calculate metrics
    total_users = len(users)
    total_images = len(images)
    
    # Filter for recent activity (last 30 days)
    recent_date = datetime.now() - timedelta(days=30)
    recent_users = [u for u in users if u[4] and u[4] > recent_date]  # created_at
    recent_images = [i for i in images if i[3] and i[3] > recent_date]  # upload_date
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", total_users, len(recent_users))
    
    with col2:
        st.metric("Total Images", total_images, len(recent_images))
    
    with col3:
        cancer_detected = len([i for i in images if i[5] and 'Cancer' in str(i[5])])
        st.metric("Cancer Cases Detected", cancer_detected)
    
    with col4:
        avg_confidence = 0
        confidence_scores = [i[6] for i in images if i[6] is not None]
        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
        st.metric("Avg Confidence", f"{avg_confidence:.1%}")
    
    # Recent activity
    st.subheader("Recent Activity")
    
    if images:
        # Convert to DataFrame for easier manipulation
        df_images = pd.DataFrame(images)
        if not df_images.empty:
            df_images.columns = [
                'id', 'username', 'filename', 'upload_date', 'image_type',
                'prediction', 'confidence_score', 'analysis_date'
            ]
        
        # Show recent uploads
        recent_uploads = df_images.head(10)
        st.dataframe(recent_uploads[['username', 'filename', 'upload_date', 'prediction', 'confidence_score']])
    else:
        st.info("No images uploaded yet.")

def show_user_management():
    """Show user management interface"""
    st.subheader("User Management")
    
    users = get_all_users()
    
    if users:
        # Convert to DataFrame
        df_users = pd.DataFrame(users)
        if not df_users.empty:
            df_users.columns = ['ID', 'Username', 'Email', 'Role', 'Created At']
        
        # User statistics
        col1, col2 = st.columns(2)
        with col1:
            st.write("**User Roles Distribution**")
            role_counts = df_users['Role'].value_counts()
            fig_pie = px.pie(values=role_counts.values, names=role_counts.index, title="User Roles")
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            st.write("**User Registration Timeline**")
            df_users['Created At'] = pd.to_datetime(df_users['Created At'])
            df_users['Date'] = df_users['Created At'].dt.date
            registrations = df_users.groupby('Date').size().reset_index().rename(columns={0: 'Count'})
            fig_line = px.line(registrations, x='Date', y='Count', title="Daily Registrations")
            st.plotly_chart(fig_line, use_container_width=True)
        
        # User table with search
        st.write("**All Users**")
        search_term = st.text_input("Search users by username or email:")
        
        if search_term:
            filtered_users = df_users[
                df_users['Username'].str.contains(search_term, case=False) |
                df_users['Email'].str.contains(search_term, case=False)
            ]
        else:
            filtered_users = df_users
        
        st.dataframe(filtered_users, use_container_width=True)
    else:
        st.info("No users found in the system.")

def show_image_analysis():
    """Show image analysis interface"""
    st.subheader("Image Analysis Overview")
    
    images = get_all_images()
    
    if images:
        # Convert to DataFrame
        df_images = pd.DataFrame(images)
        if not df_images.empty:
            df_images.columns = [
                'ID', 'Username', 'Filename', 'Upload Date', 'Image Type',
                'Prediction', 'Confidence Score', 'Analysis Date'
            ]
        
        # Analysis statistics
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Prediction Distribution**")
            prediction_counts = df_images['Prediction'].value_counts()
            fig_bar = px.bar(x=prediction_counts.index, y=prediction_counts.values, 
                           title="Prediction Results")
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            st.write("**Confidence Score Distribution**")
            valid_scores = df_images['Confidence Score'].dropna()
            if not valid_scores.empty:
                fig_hist = px.histogram(valid_scores, nbins=20, title="Confidence Scores")
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.info("No confidence scores available")
        
        # Detailed image table
        st.write("**All Analyzed Images**")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            user_filter = st.selectbox("Filter by User", ["All"] + list(df_images['Username'].unique()))
        with col2:
            prediction_filter = st.selectbox("Filter by Prediction", ["All"] + list(df_images['Prediction'].dropna().unique()))
        with col3:
            min_confidence = st.slider("Minimum Confidence", 0.0, 1.0, 0.0)
        
        # Apply filters
        filtered_df = df_images.copy()
        if user_filter != "All":
            filtered_df = filtered_df[filtered_df['Username'] == user_filter]
        if prediction_filter != "All":
            filtered_df = filtered_df[filtered_df['Prediction'] == prediction_filter]
        if min_confidence > 0:
            filtered_df = filtered_df[filtered_df['Confidence Score'] >= min_confidence]
        
        # Display filtered results
        st.dataframe(filtered_df, use_container_width=True)
        
        # Image viewer
        st.write("**Image Viewer**")
        if len(filtered_df) > 0:
            selected_image_id = st.selectbox("Select Image to View", filtered_df['ID'].tolist())
            
            if st.button("Load Image"):
                image_data = get_image_data(selected_image_id)
                if image_data:
                    image_bytes, filename, image_type = image_data
                    
                    # Display image
                    try:
                        image = Image.open(io.BytesIO(image_bytes))
                        st.image(image, caption=f"Image: {filename}", use_column_width=True)
                        
                        # Show image details
                        mask = filtered_df['ID'] == selected_image_id
                        matching_rows = filtered_df[mask]
                        if len(matching_rows) > 0:
                            selected_row = matching_rows.iloc[0]
                            st.write("**Image Details:**")
                            st.write(f"- **User:** {selected_row['Username']}")
                            st.write(f"- **Filename:** {selected_row['Filename']}")
                            st.write(f"- **Upload Date:** {selected_row['Upload Date']}")
                            st.write(f"- **Prediction:** {selected_row['Prediction']}")
                            st.write(f"- **Confidence:** {selected_row['Confidence Score']:.2%}" if pd.notna(selected_row['Confidence Score']) else "- **Confidence:** N/A")
                        else:
                            st.error("Selected image not found in filtered results")
                        
                    except Exception as e:
                        st.error(f"Error loading image: {e}")
                else:
                    st.error("Image not found or could not be loaded")
    else:
        st.info("No images found in the system.")

def show_system_statistics():
    """Show system statistics and analytics"""
    st.subheader("System Statistics")
    
    users = get_all_users()
    images = get_all_images()
    
    if not images:
        st.info("No data available for statistics.")
        return
    
    # Convert to DataFrame
    df_images = pd.DataFrame(images)
    if not df_images.empty:
        df_images.columns = [
            'ID', 'Username', 'Filename', 'Upload Date', 'Image Type',
            'Prediction', 'Confidence Score', 'Analysis Date'
        ]
    
    # Time-based analysis
    st.write("**Upload Activity Over Time**")
    df_images['Upload Date'] = pd.to_datetime(df_images['Upload Date'])
    df_images['Date'] = df_images['Upload Date'].dt.date
    
    daily_uploads = df_images.groupby('Date').size().reset_index().rename(columns={0: 'Uploads'})
    fig_timeline = px.line(daily_uploads, x='Date', y='Uploads', title="Daily Upload Activity")
    st.plotly_chart(fig_timeline, use_container_width=True)
    
    # User activity analysis
    st.write("**User Activity Analysis**")
    user_activity = df_images.groupby('Username').size().reset_index().rename(columns={0: 'Images Uploaded'})
    user_activity = user_activity.sort_values(by='Images Uploaded', ascending=False)
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Top Active Users**")
        st.dataframe(user_activity.head(10))
    
    with col2:
        st.write("**User Activity Distribution**")
        fig_user_activity = px.bar(user_activity.head(10), x='Username', y='Images Uploaded')
        st.plotly_chart(fig_user_activity, use_container_width=True)
    
    # Confidence score analysis
    st.write("**Model Performance Analysis**")
    valid_scores = df_images['Confidence Score'].dropna()
    
    if not valid_scores.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Confidence Score Statistics**")
            st.write(f"- **Mean Confidence:** {valid_scores.mean():.2%}")
            st.write(f"- **Median Confidence:** {valid_scores.median():.2%}")
            st.write(f"- **Standard Deviation:** {valid_scores.std():.2%}")
            st.write(f"- **High Confidence (>80%):** {(valid_scores > 0.8).sum()} images")
            st.write(f"- **Low Confidence (<60%):** {(valid_scores < 0.6).sum()} images")
        
        with col2:
            st.write("**Confidence by Prediction Type**")
            confidence_by_prediction = df_images.groupby('Prediction')['Confidence Score'].agg(['mean', 'count']).round(3)
            st.dataframe(confidence_by_prediction)
    
    # System health indicators
    st.write("**System Health Indicators**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_analyses = len(df_images[df_images['Prediction'].notna()])
        success_rate = (total_analyses / len(df_images)) * 100 if len(df_images) > 0 else 0
        st.metric("Analysis Success Rate", f"{success_rate:.1f}%")
    
    with col2:
        avg_confidence = valid_scores.mean() if not valid_scores.empty else 0
        st.metric("Average Model Confidence", f"{avg_confidence:.1%}")
    
    with col3:
        active_users = len(df_images['Username'].unique())
        st.metric("Active Users", active_users)

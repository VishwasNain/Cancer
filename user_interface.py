import streamlit as st
import numpy as np
import cv2
from PIL import Image
import io
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime

from image_processor import (
    process_uploaded_image, preprocess_medical_image, 
    enhance_image_for_display, create_annotated_image,
    validate_medical_image, resize_image_for_analysis
)
from ml_model import analyze_lung_image
from database import store_image, store_analysis_result, get_user_images

def show_user_interface():
    """Display user interface for medical image analysis"""
    st.header(f"🫁 Lung Cancer Detection - Welcome {st.session_state.username}")
    
    # Create tabs for different user functions
    tab1, tab2, tab3 = st.tabs(["Upload & Analyze", "My Results", "Medical Information"])
    
    with tab1:
        show_image_upload_interface()
    
    with tab2:
        show_user_results()
    
    with tab3:
        show_medical_information()

def show_image_upload_interface():
    """Show image upload and analysis interface"""
    st.subheader("📤 Upload Medical Image for Analysis")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a medical image (X-ray, CT scan)",
        type=['png', 'jpg', 'jpeg', 'tiff', 'bmp'],
        help="Upload a lung X-ray or CT scan image for cancer detection analysis"
    )
    
    if uploaded_file is not None:
        # Process the uploaded image
        image_array, image_data, file_info = process_uploaded_image(uploaded_file)
        
        if image_array is not None:
            # Display image information
            col1, col2 = st.columns([2, 1])
            
            with col1:
                filename = file_info.get('filename', 'Unknown') if file_info else 'Unknown'
                st.image(image_array, caption=f"Uploaded: {filename}", use_column_width=True)
            
            with col2:
                st.write("**Image Information:**")
                if file_info:
                    st.write(f"- **Filename:** {file_info.get('filename', 'Unknown')}")
                    if file_info.get('dimensions'):
                        st.write(f"- **Dimensions:** {file_info['dimensions'][0]} x {file_info['dimensions'][1]}")
                    else:
                        st.write(f"- **Dimensions:** Unknown")
                    st.write(f"- **File Size:** {file_info.get('size', 0) / 1024:.1f} KB")
                    st.write(f"- **Format:** {file_info.get('format', 'Unknown')}")
                else:
                    st.write("- **File information not available**")
            
            # Validate image
            validation_result = validate_medical_image(image_array, file_info)
            
            # Show validation results
            if validation_result['warnings']:
                for warning in validation_result['warnings']:
                    st.warning(f"⚠️ {warning}")
            
            if validation_result['errors']:
                for error in validation_result['errors']:
                    st.error(f"❌ {error}")
            
            # Analysis button
            if validation_result['is_valid']:
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    analyze_button = st.button("🔍 Analyze Image", type="primary", use_container_width=True)
                
                if analyze_button:
                    analyze_and_display_results(image_array, image_data, file_info)
            else:
                st.error("Cannot analyze image due to validation errors. Please upload a different image.")
        else:
            st.error("Failed to process the uploaded image. Please try a different file.")

def analyze_and_display_results(image_array, image_data, file_info):
    """Analyze image and display results"""
    # Store the original image first
    image_id = store_image(
        st.session_state.user_id,
        file_info['filename'],
        image_data,
        file_info.get('format', 'Unknown'),
        file_info['size']
    )
    
    if not image_id:
        st.error("Failed to store image. Please try again.")
        return
    
    # Show progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Preprocess image
        status_text.text("Preprocessing image...")
        progress_bar.progress(25)
        
        preprocessed_image = preprocess_medical_image(image_array)
        
        # Resize for analysis
        status_text.text("Preparing for analysis...")
        progress_bar.progress(50)
        
        analysis_image = resize_image_for_analysis(preprocessed_image)
        
        # Perform ML analysis
        status_text.text("Analyzing with AI model...")
        progress_bar.progress(75)
        
        analysis_result = analyze_lung_image(analysis_image)
        
        # Store analysis result
        status_text.text("Storing results...")
        progress_bar.progress(90)
        
        result_id = store_analysis_result(
            image_id,
            st.session_state.user_id,
            analysis_result['prediction'],
            analysis_result['confidence'],
            analysis_result['detailed_results'],
            analysis_result['processing_time']
        )
        
        progress_bar.progress(100)
        status_text.text("Analysis complete!")
        
        if result_id:
            # Display results
            display_analysis_results(image_array, analysis_result)
        else:
            st.error("Failed to store analysis results.")
            
    except Exception as e:
        st.error(f"Analysis failed: {str(e)}")
    finally:
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()

def display_analysis_results(image_array, analysis_result):
    """Display comprehensive analysis results"""
    st.success("✅ Analysis Complete!")
    
    # Main results
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🔍 Analysis Results")
        
        # Prediction with appropriate styling
        prediction = analysis_result['prediction']
        confidence = analysis_result['confidence']
        
        if 'Cancer' in prediction:
            st.error(f"⚠️ **{prediction}**")
        else:
            st.success(f"✅ **{prediction}**")
        
        # Confidence score
        st.metric("Confidence Score", f"{confidence:.1%}")
        
        # Risk level
        risk_level = analysis_result['risk_level']
        if 'High Risk' in risk_level:
            st.error(f"🚨 **Risk Level:** {risk_level}")
        elif 'Moderate Risk' in risk_level:
            st.warning(f"⚠️ **Risk Level:** {risk_level}")
        else:
            st.info(f"ℹ️ **Risk Level:** {risk_level}")
        
        # Processing time
        processing_time = analysis_result['processing_time']
        st.info(f"⏱️ **Processing Time:** {processing_time:.2f} seconds")
    
    with col2:
        st.subheader("📊 Confidence Visualization")
        
        # Create gauge chart for confidence
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = confidence * 100,
            title = {'text': "Confidence Score (%)"},
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_gauge.update_layout(height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    # Detailed results
    if 'detailed_results' in analysis_result and analysis_result['detailed_results']:
        st.subheader("📋 Detailed Analysis")
        
        detailed = analysis_result['detailed_results']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Image Quality Assessment:**")
            st.write(f"- Quality: {detailed.get('image_quality', 'Unknown')}")
            st.write(f"- Mean Intensity: {detailed.get('mean_intensity', 0):.1f}")
            st.write(f"- Intensity Variation: {detailed.get('intensity_variation', 0):.1f}")
        
        with col2:
            st.write("**Structural Analysis:**")
            st.write(f"- Potential Nodules: {detailed.get('potential_nodules_count', 0)}")
            st.write(f"- Texture Complexity: {detailed.get('texture_complexity', 0):.3f}")
            st.write(f"- Edge Density: {detailed.get('edge_density', 0):.3f}")
        
        # Analysis notes
        if 'analysis_notes' in detailed:
            st.write("**Clinical Notes:**")
            st.info(detailed['analysis_notes'])
    
    # Enhanced image display
    st.subheader("🖼️ Enhanced Image Analysis")
    
    # Create side-by-side comparison
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Original Image**")
        st.image(image_array, use_column_width=True)
    
    with col2:
        st.write("**Enhanced Image**")
        enhanced_image = enhance_image_for_display(image_array)
        st.image(enhanced_image, use_column_width=True)
    
    # Annotated image
    st.write("**Annotated Analysis**")
    annotated_image = create_annotated_image(image_array, analysis_result)
    st.image(annotated_image, use_column_width=True)
    
    # Recommendations
    st.subheader("🩺 Medical Recommendations")
    
    if 'Cancer' in prediction:
        st.error("""
        **⚠️ IMPORTANT NOTICE:**
        - This analysis suggests potential abnormalities that require immediate medical attention
        - Please consult with an oncologist or radiologist as soon as possible
        - This AI analysis is a screening tool and should not replace professional medical diagnosis
        - Further diagnostic tests (biopsy, additional imaging) may be required
        """)
    else:
        st.success("""
        **✅ GOOD NEWS:**
        - The analysis shows no obvious signs of malignancy
        - Continue with regular screening as recommended by your healthcare provider
        - Maintain healthy lifestyle habits (no smoking, regular exercise)
        - Report any persistent symptoms to your doctor
        """)
    
    # Disclaimer
    st.warning("""
    **⚠️ MEDICAL DISCLAIMER:**
    This AI-powered analysis is for informational purposes only and should not be considered as a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition.
    """)

def show_user_results():
    """Show user's previous analysis results"""
    st.subheader("📊 My Analysis History")
    
    user_images = get_user_images(st.session_state.user_id)
    
    if user_images:
        # Convert to DataFrame for easier handling
        df = pd.DataFrame(user_images)
        if not df.empty:
            df.columns = [
                'Image ID', 'Filename', 'Upload Date', 'Image Type', 'File Size',
                'Prediction', 'Confidence Score', 'Analysis Date'
            ]
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Images", len(df))
        
        with col2:
            analyzed_count = len(df[df['Prediction'].notna()])
            st.metric("Analyzed Images", analyzed_count)
        
        with col3:
            if analyzed_count > 0:
                cancer_detected = len(df[df['Prediction'].notna() & df['Prediction'].str.contains('Cancer', na=False)])
                st.metric("Cancer Detected", cancer_detected)
            else:
                st.metric("Cancer Detected", 0)
        
        with col4:
            avg_confidence = df['Confidence Score'].mean() if not df.empty and len(df[df['Confidence Score'].notna()]) > 0 else 0
            st.metric("Avg Confidence", f"{avg_confidence:.1%}")
        
        # Results timeline
        if not df.empty and 'Upload Date' in df.columns and len(df[df['Upload Date'].notna()]) > 0:
            st.subheader("📈 Upload Timeline")
            
            # Prepare data for timeline
            df['Upload Date'] = pd.to_datetime(df['Upload Date'])
            timeline_data = df.groupby(df['Upload Date'].dt.date).size().reset_index().rename(columns={0: 'Count'})
            
            fig_timeline = px.line(timeline_data, x='Upload Date', y='Count', 
                                 title="Image Uploads Over Time")
            st.plotly_chart(fig_timeline, use_container_width=True)
        
        # Prediction distribution
        if not df.empty and len(df[df['Prediction'].notna()]) > 0:
            st.subheader("📊 Analysis Results Distribution")
            
            prediction_counts = df['Prediction'].value_counts()
            fig_pie = px.pie(values=prediction_counts.values, names=prediction_counts.index,
                           title="Prediction Results")
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Detailed results table
        st.subheader("📋 Detailed Results")
        
        # Display options
        col1, col2 = st.columns(2)
        with col1:
            show_all = st.checkbox("Show all columns", value=False)
        with col2:
            sort_by = st.selectbox("Sort by", ["Upload Date", "Confidence Score", "Prediction"])
        
        # Prepare display DataFrame
        if show_all:
            display_df = df
        else:
            display_df = df[['Filename', 'Upload Date', 'Prediction', 'Confidence Score']]
        
        # Sort
        if sort_by == "Upload Date" and len(display_df) > 0:
            display_df = display_df.sort_values(by='Upload Date', ascending=False)
        elif sort_by == "Confidence Score" and len(display_df) > 0:
            display_df = display_df.sort_values(by='Confidence Score', ascending=False)
        elif sort_by == "Prediction" and len(display_df) > 0:
            display_df = display_df.sort_values(by='Prediction', ascending=True)
        
        st.dataframe(display_df, use_container_width=True)
        
    else:
        st.info("No images uploaded yet. Use the 'Upload & Analyze' tab to get started!")

def show_medical_information():
    """Show medical information and educational content"""
    st.subheader("🩺 Medical Information & Education")
    
    # Educational tabs
    edu_tab1, edu_tab2, edu_tab3, edu_tab4 = st.tabs([
        "About Lung Cancer", 
        "Screening Guidelines", 
        "Understanding Results", 
        "When to Seek Help"
    ])
    
    with edu_tab1:
        st.markdown("""
        ## About Lung Cancer
        
        Lung cancer is one of the most common and serious types of cancer. It occurs when cells in the lungs grow and multiply uncontrollably, forming tumors.
        
        ### Types of Lung Cancer:
        - **Non-Small Cell Lung Cancer (NSCLC)**: About 85% of lung cancers
        - **Small Cell Lung Cancer (SCLC)**: About 15% of lung cancers
        
        ### Risk Factors:
        - **Smoking**: The leading cause (85-90% of cases)
        - **Secondhand smoke**: Increases risk by 20-30%
        - **Radon exposure**: Second leading cause
        - **Asbestos exposure**: Particularly dangerous when combined with smoking
        - **Family history**: Genetic predisposition
        - **Air pollution**: Long-term exposure
        - **Previous radiation therapy**: To the chest area
        
        ### Symptoms to Watch For:
        - Persistent cough that doesn't go away
        - Coughing up blood or rust-colored sputum
        - Chest pain that worsens with breathing or coughing
        - Shortness of breath
        - Unexplained weight loss
        - Fatigue
        - Hoarseness
        - Recurring respiratory infections
        """)
    
    with edu_tab2:
        st.markdown("""
        ## Screening Guidelines
        
        Early detection of lung cancer can significantly improve treatment outcomes and survival rates.
        
        ### Who Should Be Screened:
        The U.S. Preventive Services Task Force (USPSTF) recommends annual lung cancer screening for people who:
        - Are 50-80 years old
        - Have a 20 pack-year smoking history (pack-year = packs per day × years smoked)
        - Currently smoke or have quit within the past 15 years
        - Are in good health and able to undergo treatment if cancer is found
        
        ### Screening Methods:
        - **Low-Dose CT (LDCT)**: The gold standard for lung cancer screening
        - **Chest X-rays**: Less sensitive but still useful for initial assessment
        - **Sputum cytology**: Analysis of coughed-up phlegm
        
        ### AI-Assisted Screening:
        - Our system uses machine learning to analyze medical images
        - Provides preliminary assessment and confidence scores
        - Helps identify areas that may need closer examination
        - **Important**: AI screening is supplementary to, not a replacement for, professional medical evaluation
        """)
    
    with edu_tab3:
        st.markdown("""
        ## Understanding Your Results
        
        ### Prediction Types:
        - **Normal**: No obvious signs of malignancy detected
        - **Cancer Detected**: Suspicious patterns identified that may indicate cancer
        
        ### Confidence Scores:
        - **90-100%**: Very high confidence in the prediction
        - **70-89%**: High confidence, reliable result
        - **50-69%**: Moderate confidence, may need additional testing
        - **Below 50%**: Low confidence, results uncertain
        
        ### Risk Levels:
        - **Very Low Risk**: Normal findings with high confidence
        - **Low Risk**: Normal findings with moderate confidence
        - **Moderate Risk**: Some concerning features detected
        - **High Risk**: Strong indicators of potential malignancy
        - **Uncertain**: Requires additional imaging or testing
        
        ### What Affects Analysis Quality:
        - **Image quality**: Clear, high-resolution images provide better results
        - **Patient positioning**: Proper positioning improves accuracy
        - **Image type**: CT scans generally provide more detail than X-rays
        - **Technical factors**: Proper exposure and contrast settings
        
        ### Limitations:
        - AI analysis is a screening tool, not a diagnostic tool
        - Small or early-stage cancers may not be detected
        - False positives and false negatives can occur
        - Cannot replace radiologist interpretation
        """)
    
    with edu_tab4:
        st.markdown("""
        ## When to Seek Immediate Medical Help
        
        ### Urgent Symptoms (Seek immediate care):
        - **Severe chest pain**: Especially if sudden or worsening
        - **Difficulty breathing**: Shortness of breath at rest
        - **Coughing up blood**: Any amount of blood in sputum
        - **Severe, persistent cough**: Especially if new or changing
        - **Unexplained weight loss**: 10+ pounds without trying
        - **Severe fatigue**: That interferes with daily activities
        
        ### Follow-up Required If:
        - AI analysis shows "Cancer Detected"
        - Confidence score is high (>70%) for abnormal findings
        - You have persistent symptoms lasting more than 2-3 weeks
        - You have risk factors and concerning symptoms
        
        ### Questions to Ask Your Doctor:
        1. "What do my scan results mean?"
        2. "Do I need additional testing?"
        3. "What are my risk factors?"
        4. "How often should I be screened?"
        5. "What symptoms should I watch for?"
        6. "Are there lifestyle changes I should make?"
        
        ### Emergency Contacts:
        - **Emergency**: Call 911 for severe breathing problems
        - **Primary Care**: For non-emergency follow-up
        - **Oncology**: If cancer is suspected or confirmed
        - **Pulmonology**: For lung-specific concerns
        
        ### Resources:
        - American Lung Association: lung.org
        - National Cancer Institute: cancer.gov
        - American Cancer Society: cancer.org
        - Lung Cancer Research Foundation: lcrf.org
        """)
    
    # Disclaimer
    st.error("""
    **⚠️ IMPORTANT MEDICAL DISCLAIMER**
    
    The information provided here is for educational purposes only and should not be used as a substitute for professional medical advice, diagnosis, or treatment. Always consult with qualified healthcare providers for medical decisions and treatment options.
    
    This AI screening tool is designed to assist in the early detection process but cannot replace professional radiological interpretation or comprehensive medical evaluation.
    """)

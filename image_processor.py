import cv2
import numpy as np
from PIL import Image
import io
import base64

def process_uploaded_image(uploaded_file):
    """Process uploaded image file"""
    try:
        # Read the uploaded file
        image_data = uploaded_file.read()
        
        # Convert to PIL Image
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array
        image_array = np.array(image)
        
        # Get file info
        file_info = {
            'filename': uploaded_file.name,
            'size': len(image_data),
            'format': image.format if hasattr(image, 'format') else 'Unknown',
            'dimensions': image.size
        }
        
        return image_array, image_data, file_info
        
    except Exception as e:
        print(f"Error processing image: {e}")
        return None, None, None

def preprocess_medical_image(image):
    """Preprocess medical image for analysis"""
    try:
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Apply histogram equalization to improve contrast
        equalized = cv2.equalizeHist(gray)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(equalized, (3, 3), 0)
        
        # Normalize to 0-255 range
        normalized = cv2.normalize(blurred, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        
        return normalized
        
    except Exception as e:
        print(f"Error preprocessing image: {e}")
        return image

def enhance_image_for_display(image):
    """Enhance image for better visualization"""
    try:
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        if len(image.shape) == 3:
            # For color images, apply CLAHE to the L channel in LAB color space
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            lab[:, :, 0] = clahe.apply(lab[:, :, 0])
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        else:
            # For grayscale images
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(image)
        
        return enhanced
        
    except Exception as e:
        print(f"Error enhancing image: {e}")
        return image

def create_annotated_image(image, analysis_result):
    """Create annotated image with analysis results"""
    try:
        # Create a copy of the original image
        annotated = image.copy()
        
        # Convert to RGB if grayscale
        if len(annotated.shape) == 2:
            annotated = cv2.cvtColor(annotated, cv2.COLOR_GRAY2RGB)
        
        # Add text annotations
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        
        # Prediction text
        prediction_text = analysis_result.get('prediction', 'Unknown')
        confidence = analysis_result.get('confidence', 0.0)
        
        # Choose color based on prediction
        if 'Cancer' in prediction_text:
            text_color = (255, 0, 0)  # Red for cancer detection
        else:
            text_color = (0, 255, 0)  # Green for normal
        
        # Add prediction text
        cv2.putText(annotated, f"Prediction: {prediction_text}", 
                   (10, 30), font, font_scale, text_color, thickness)
        
        # Add confidence score
        cv2.putText(annotated, f"Confidence: {confidence:.2%}", 
                   (10, 60), font, font_scale, text_color, thickness)
        
        # Add risk level
        risk_level = analysis_result.get('risk_level', 'Unknown')
        cv2.putText(annotated, f"Risk: {risk_level}", 
                   (10, 90), font, font_scale, text_color, thickness)
        
        return annotated
        
    except Exception as e:
        print(f"Error creating annotated image: {e}")
        return image

def validate_medical_image(image_array, file_info):
    """Validate if the uploaded image is suitable for medical analysis"""
    try:
        validations = {
            'is_valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Check image dimensions
        height, width = image_array.shape[:2]
        
        if height < 100 or width < 100:
            validations['errors'].append("Image resolution too low (minimum 100x100 pixels)")
            validations['is_valid'] = False
        
        if height > 4000 or width > 4000:
            validations['warnings'].append("Very high resolution image - processing may be slow")
        
        # Check file size
        file_size_mb = file_info['size'] / (1024 * 1024)
        if file_size_mb > 50:
            validations['warnings'].append("Large file size - processing may be slow")
        
        # Check if image appears to be medical (basic heuristics)
        gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY) if len(image_array.shape) == 3 else image_array
        
        # Check contrast
        contrast = np.std(gray)
        if contrast < 20:
            validations['warnings'].append("Low contrast image - results may be less reliable")
        
        # Check for very dark or very bright images
        mean_brightness = np.mean(gray)
        if mean_brightness < 30:
            validations['warnings'].append("Very dark image - may affect analysis accuracy")
        elif mean_brightness > 225:
            validations['warnings'].append("Very bright image - may affect analysis accuracy")
        
        return validations
        
    except Exception as e:
        return {
            'is_valid': False,
            'warnings': [],
            'errors': [f"Image validation failed: {str(e)}"]
        }

def convert_image_to_base64(image):
    """Convert image to base64 string for storage/display"""
    try:
        # Convert numpy array to PIL Image
        if isinstance(image, np.ndarray):
            if len(image.shape) == 2:  # Grayscale
                pil_image = Image.fromarray(image, mode='L')
            else:  # RGB
                pil_image = Image.fromarray(image, mode='RGB')
        else:
            pil_image = image
        
        # Convert to base64
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return img_base64
        
    except Exception as e:
        print(f"Error converting image to base64: {e}")
        return None

def resize_image_for_analysis(image, max_size=512):
    """Resize image for faster analysis while maintaining aspect ratio"""
    try:
        height, width = image.shape[:2]
        
        # Calculate scaling factor
        scale = min(max_size / width, max_size / height)
        
        if scale < 1:
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            if len(image.shape) == 3:
                resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            else:
                resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            return resized
        
        return image
        
    except Exception as e:
        print(f"Error resizing image: {e}")
        return image

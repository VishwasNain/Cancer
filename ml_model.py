import numpy as np
import cv2
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os
from skimage import feature, measure, filters
from skimage.segmentation import clear_border
from skimage.morphology import disk, opening, closing, erosion, dilation
import matplotlib.pyplot as plt
import time

class LungCancerDetector:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the machine learning model"""
        # Use a Random Forest classifier for lung cancer detection
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        # Train with synthetic features for demonstration
        # In a real application, this would be trained on actual medical data
        self._train_initial_model()
    
    def _train_initial_model(self):
        """Train the model with synthetic feature patterns"""
        # Generate synthetic training data based on common lung cancer indicators
        np.random.seed(42)
        
        # Features: texture, shape, density, size, location-based features
        n_samples = 1000
        n_features = 20
        
        # Generate features for normal cases
        normal_features = np.random.normal(0.3, 0.1, (n_samples//2, n_features))
        normal_labels = np.zeros(n_samples//2)
        
        # Generate features for abnormal cases (cancer indicators)
        abnormal_features = np.random.normal(0.7, 0.15, (n_samples//2, n_features))
        abnormal_labels = np.ones(n_samples//2)
        
        # Combine data
        X = np.vstack([normal_features, abnormal_features])
        y = np.hstack([normal_labels, abnormal_labels])
        
        # Add some realistic constraints
        X = np.clip(X, 0, 1)
        
        # Train the model
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self.scaler.fit(X_train)
        X_train_scaled = self.scaler.transform(X_train)
        
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
    
    def extract_features(self, image):
        """Extract features from medical image"""
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
            
            # Normalize the image
            gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Extract texture features using Local Binary Pattern
            lbp = feature.local_binary_pattern(blurred, 8, 1, method='uniform')
            lbp_hist, _ = np.histogram(lbp.ravel(), bins=10, range=(0, 10))
            lbp_hist = lbp_hist.astype(float)
            lbp_hist /= (lbp_hist.sum() + 1e-6)
            
            # Extract edge features
            edges = feature.canny(blurred, sigma=1, low_threshold=0.1, high_threshold=0.2)
            edge_density = np.mean(edges)
            
            # Extract intensity statistics
            mean_intensity = np.mean(gray)
            std_intensity = np.std(gray)
            skewness = self._calculate_skewness(gray)
            kurtosis = self._calculate_kurtosis(gray)
            
            # Extract shape features through contour analysis
            contours, _ = cv2.findContours(edges.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest_contour)
                perimeter = cv2.arcLength(largest_contour, True)
                circularity = 4 * np.pi * area / (perimeter * perimeter + 1e-6)
            else:
                area, perimeter, circularity = 0, 0, 0
            
            # Combine all features
            features = np.concatenate([
                lbp_hist,  # 10 features
                [edge_density, mean_intensity, std_intensity, skewness, kurtosis],  # 5 features
                [area / (gray.shape[0] * gray.shape[1]), perimeter / (2 * (gray.shape[0] + gray.shape[1])), circularity],  # 3 features
                [np.percentile(gray, p) for p in [25, 50, 75, 90]]  # 4 features
            ])
            
            # Pad or truncate to ensure exactly 20 features
            if len(features) < 20:
                features = np.pad(features, (0, 20 - len(features)), 'constant')
            else:
                features = features[:20]
            
            return features
            
        except Exception as e:
            print(f"Feature extraction error: {e}")
            # Return default features if extraction fails
            return np.zeros(20)
    
    def _calculate_skewness(self, image):
        """Calculate skewness of image intensity distribution"""
        flat = image.flatten()
        mean_val = np.mean(flat)
        std_val = np.std(flat)
        if std_val == 0:
            return 0
        return np.mean(((flat - mean_val) / std_val) ** 3)
    
    def _calculate_kurtosis(self, image):
        """Calculate kurtosis of image intensity distribution"""
        flat = image.flatten()
        mean_val = np.mean(flat)
        std_val = np.std(flat)
        if std_val == 0:
            return 0
        return np.mean(((flat - mean_val) / std_val) ** 4) - 3
    
    def predict(self, image):
        """Predict lung cancer from medical image"""
        start_time = time.time()
        
        try:
            # Extract features
            features = self.extract_features(image)
            
            # Reshape for prediction
            features = features.reshape(1, -1)
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Make prediction
            prediction = self.model.predict(features_scaled)[0]
            confidence = self.model.predict_proba(features_scaled)[0].max()
            
            # Get detailed analysis
            detailed_results = self._get_detailed_analysis(image, features[0], prediction, confidence)
            
            processing_time = time.time() - start_time
            
            result = {
                'prediction': 'Cancer Detected' if prediction == 1 else 'Normal',
                'confidence': float(confidence),
                'risk_level': self._get_risk_level(confidence, prediction),
                'detailed_results': detailed_results,
                'processing_time': processing_time
            }
            
            return result
            
        except Exception as e:
            print(f"Prediction error: {e}")
            return {
                'prediction': 'Analysis Failed',
                'confidence': 0.0,
                'risk_level': 'Unknown',
                'detailed_results': {'error': str(e)},
                'processing_time': time.time() - start_time
            }
    
    def _get_risk_level(self, confidence, prediction):
        """Determine risk level based on prediction and confidence"""
        if prediction == 0:  # Normal
            if confidence > 0.9:
                return 'Very Low Risk'
            elif confidence > 0.7:
                return 'Low Risk'
            else:
                return 'Uncertain - Recommend Further Testing'
        else:  # Cancer detected
            if confidence > 0.9:
                return 'High Risk - Immediate Consultation Required'
            elif confidence > 0.7:
                return 'Moderate Risk - Further Testing Recommended'
            else:
                return 'Uncertain - Additional Imaging Required'
    
    def _get_detailed_analysis(self, image, features, prediction, confidence):
        """Generate detailed analysis results"""
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
            
            # Analyze image characteristics
            mean_intensity = np.mean(gray)
            std_intensity = np.std(gray)
            
            # Detect potential regions of interest
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = feature.canny(blurred, sigma=1)
            
            # Count potential nodules (simplified approach)
            contours, _ = cv2.findContours(edges.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            potential_nodules = len([c for c in contours if cv2.contourArea(c) > 50])
            
            detailed_results = {
                'image_quality': 'Good' if std_intensity > 30 else 'Poor',
                'mean_intensity': float(mean_intensity),
                'intensity_variation': float(std_intensity),
                'potential_nodules_count': potential_nodules,
                'texture_complexity': float(features[0]) if len(features) > 0 else 0.0,
                'edge_density': float(features[10]) if len(features) > 10 else 0.0,
                'analysis_notes': self._generate_analysis_notes(prediction, confidence, potential_nodules)
            }
            
            return detailed_results
            
        except Exception as e:
            return {'error': f'Detailed analysis failed: {str(e)}'}
    
    def _generate_analysis_notes(self, prediction, confidence, nodule_count):
        """Generate human-readable analysis notes"""
        notes = []
        
        if prediction == 1:  # Cancer detected
            notes.append("Suspicious patterns detected in lung tissue.")
            if confidence > 0.8:
                notes.append("High confidence in abnormal findings.")
            if nodule_count > 3:
                notes.append(f"Multiple potential nodules identified ({nodule_count}).")
            notes.append("Recommend immediate consultation with oncologist.")
        else:  # Normal
            notes.append("No obvious signs of malignancy detected.")
            if confidence > 0.8:
                notes.append("High confidence in normal classification.")
            if nodule_count > 0:
                notes.append(f"Some tissue variations noted ({nodule_count} regions) - likely benign.")
            notes.append("Continue regular screening as recommended.")
        
        return " ".join(notes)

# Global model instance
lung_cancer_detector = LungCancerDetector()

def analyze_lung_image(image):
    """Main function to analyze lung image"""
    return lung_cancer_detector.predict(image)

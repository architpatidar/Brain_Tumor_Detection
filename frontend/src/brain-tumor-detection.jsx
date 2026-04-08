import React, { useEffect, useState } from 'react';
import axios from 'axios';
import {
  Upload, MapPin, Calendar, User, Lock, Mail, Phone,
  AlertCircle, CheckCircle, Activity, Download, Clock,
  Star, Building2, Stethoscope, Brain, Shield
} from 'lucide-react';

// ─── Constants (outside component so they never re-create) ────────────────────

const theme = {
  primary: '#0A4D68',
  secondary: '#088395',
  accent: '#05BFDB',
  success: '#07BC0C',
  warning: '#F1C40F',
  danger: '#E74C3C',
  lightBg: '#F0F8FF',
  darkText: '#1A1A2E',
};

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const buildMapEmbedUrl = ({ lat, lng, query }) => {
  if (lat != null && lng != null) {
    return `https://www.google.com/maps?q=${lat},${lng}&z=12&output=embed`;
  }
  return `https://www.google.com/maps?q=${encodeURIComponent(query)}&output=embed`;
};

const normalizeDetectionResult = result => ({
  ...result,
  type: result?.tumor_type ?? result?.type ?? null,
});

const navBtnStyle = {
  background: 'rgba(255,255,255,0.15)',
  border: 'none',
  color: 'white',
  padding: '0.6rem 1.2rem',
  borderRadius: '8px',
  cursor: 'pointer',
  fontSize: '0.95rem',
  fontWeight: 500,
  transition: 'all 0.2s ease',
};

const labelStyle = {
  fontSize: '0.9rem',
  fontWeight: 600,
  color: '#1A1A2E',
  marginBottom: '0.5rem',
  display: 'block',
};

const inputRowStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '0.75rem',
  padding: '0.85rem 1rem',
  border: '2px solid #E0E0E0',
  borderRadius: '10px',
  background: 'white',
};

const inputStyle = {
  border: 'none',
  outline: 'none',
  flex: 1,
  fontSize: '1rem',
  background: 'transparent',
  fontFamily: 'Inter, sans-serif',
};

const submitBtnStyle = {
  width: '100%',
  background: 'linear-gradient(135deg,#0A4D68,#088395)',
  color: 'white',
  border: 'none',
  padding: '1rem',
  borderRadius: '10px',
  fontSize: '1rem',
  fontWeight: 600,
  cursor: 'pointer',
  fontFamily: 'Poppins, sans-serif',
  boxShadow: '0 8px 20px rgba(8,131,149,0.3)',
};

const linkBtnStyle = {
  background: 'transparent',
  border: 'none',
  color: '#088395',
  fontSize: '0.95rem',
  fontWeight: 600,
  cursor: 'pointer',
};

const mockDoctors = [
  { id: 1, name: 'Dr. Sarah Mitchell', specialization: 'Neurological Surgeon', experience: 15, rating: 4.9, contact: '+91-1234567890', hospital: 'Apollo Hospital', city: 'Jaipur', image: '👨‍⚕️', availability: ['Mon', 'Wed', 'Fri'] },
  { id: 2, name: 'Dr. Rajesh Kumar', specialization: 'Neuro-Oncologist', experience: 12, rating: 4.8, contact: '+91-2345678912', hospital: 'Fortis Healthcare', city: 'Jaipur', image: '👨‍⚕️', availability: ['Tue', 'Thu', 'Sat'] },
  { id: 3, name: 'Dr. Priya Sharma', specialization: 'Radiologist', experience: 10, rating: 4.7, contact: '+91-3456789123', hospital: 'Max Hospital', city: 'Jaipur', image: '👩‍⚕️', availability: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'] },
  { id: 4, name: 'Dr. Amit Verma', specialization: 'Neurologist', experience: 18, rating: 4.9, contact: '+91-4567891334', hospital: 'AIIMS Jaipur', city: 'Jaipur', image: '👨‍⚕️', availability: ['Wed', 'Thu', 'Fri'] },
];



// ─── Page: Home ───────────────────────────────────────────────────────────────
const HomePage = ({ isLoggedIn, setCurrentPage }) => (
  <div style={{ minHeight: '100vh', background: 'linear-gradient(180deg,#F0F8FF,#E6F3FF)', padding: '3rem 2rem' }}>
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{
        background: 'linear-gradient(135deg,#0A4D68,#088395,#05BFDB)',
        borderRadius: '24px', padding: '4rem', color: 'white',
        marginBottom: '3rem', boxShadow: '0 20px 60px rgba(8,131,149,0.3)',
        position: 'relative', overflow: 'hidden'
      }}>
        <div style={{ position: 'absolute', top: '-50px', right: '-50px', width: '300px', height: '300px', background: 'radial-gradient(circle,rgba(5,191,219,0.3),transparent 70%)', borderRadius: '50%' }} />
        <div style={{ position: 'relative', zIndex: 1 }}>
          <h1 style={{ fontSize: '3rem', fontWeight: 800, lineHeight: 1.2, marginBottom: '1rem' }}>
            Advanced AI-Powered<br />Brain Tumor Detection
          </h1>
          <p style={{ fontSize: '1.2rem', marginBottom: '2rem', opacity: 0.95, maxWidth: '650px' }}>
            Upload your MRI, CT, or X-ray scans for instant AI analysis. Connect with top neurologists near you.
          </p>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <button onClick={() => setCurrentPage(isLoggedIn ? 'detect' : 'auth')} style={{ background: 'white', color: theme.primary, border: 'none', padding: '1rem 2.5rem', borderRadius: '12px', fontSize: '1.05rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Upload size={20} /> Start Scan
            </button>
            <button onClick={() => setCurrentPage('doctors')} style={{ background: 'rgba(255,255,255,0.2)', color: 'white', border: '2px solid white', padding: '1rem 2.5rem', borderRadius: '12px', fontSize: '1.05rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Stethoscope size={20} /> Find Doctors
            </button>
          </div>
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(260px,1fr))', gap: '1.5rem', marginBottom: '3rem' }}>
        {[
          { Icon: Brain, title: 'AI Detection', desc: '94% accuracy in tumor identification', color: '#088395' },
          { Icon: Stethoscope, title: 'Expert Doctors', desc: 'Connect with certified neurologists', color: '#07BC0C' },
          { Icon: Calendar, title: 'Easy Booking', desc: 'Schedule appointments instantly', color: '#05BFDB' },
          { Icon: Shield, title: 'Secure & Private', desc: 'Your medical data is encrypted', color: '#0A4D68' },
        ].map(({ Icon, title, desc, color }, i) => (
          <div key={i} style={{ background: 'white', padding: '2rem', borderRadius: '16px', boxShadow: '0 4px 20px rgba(0,0,0,0.08)' }}>
            <Icon size={46} color={color} strokeWidth={1.5} />
            <h3 style={{ fontSize: '1.2rem', margin: '1rem 0 0.4rem', color: theme.darkText }}>{title}</h3>
            <p style={{ color: '#666', fontSize: '0.95rem' }}>{desc}</p>
          </div>
        ))}
      </div>
      <div style={{ background: 'white', borderRadius: '20px', padding: '2.5rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(180px,1fr))', gap: '2rem', boxShadow: '0 4px 20px rgba(0,0,0,0.08)' }}>
        {[['50,000+', 'Scans Analyzed'], ['200+', 'Expert Doctors'], ['94%', 'Detection Accuracy'], ['4.8★', 'User Rating']].map(([val, lbl], i) => (
          <div key={i} style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '2.5rem', fontWeight: 800, color: theme.primary }}>{val}</div>
            <div style={{ color: '#666', marginTop: '0.4rem' }}>{lbl}</div>
          </div>
        ))}
      </div>
    </div>
  </div>
);

// ─── Page: Auth ───────────────────────────────────────────────────────────────
const AuthPage = ({ authMode, setAuthMode, loginData, setLoginData, signupData, setSignupData,
  resetEmail, setResetEmail, handleLogin, handleSignup, handlePasswordReset }) => (
  <div style={{ minHeight: '100vh', background: 'linear-gradient(135deg,#0A4D68,#088395)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
    <div style={{ background: 'white', borderRadius: '20px', padding: '3rem', width: '100%', maxWidth: '440px', boxShadow: '0 20px 60px rgba(0,0,0,0.3)' }}>
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <Brain size={48} color={theme.primary} style={{ margin: '0 auto' }} />
        <h2 style={{ fontSize: '1.8rem', color: theme.darkText, margin: '1rem 0 0.4rem', fontWeight: 700 }}>
          {authMode === 'login' ? 'Welcome Back' : authMode === 'signup' ? 'Create Account' : 'Reset Password'}
        </h2>
        <p style={{ color: '#666', fontSize: '0.95rem' }}>
          {authMode === 'login' ? 'Sign in to your health dashboard' : authMode === 'signup' ? 'Join thousands protecting their health' : 'Enter your email for reset instructions'}
        </p>
      </div>

      {authMode === 'login' && (
        <form onSubmit={handleLogin}>
          <div style={{ marginBottom: '1.2rem' }}>
            <label style={labelStyle}>Email Address</label>
            <div style={inputRowStyle}>
              <Mail size={20} color="#888" />
              <input type="email" placeholder="your@email.com" style={inputStyle} required
                value={loginData.email}
                onChange={e => setLoginData(prev => ({ ...prev, email: e.target.value }))}
              />
            </div>
          </div>
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={labelStyle}>Password</label>
            <div style={inputRowStyle}>
              <Lock size={20} color="#888" />
              <input type="password" placeholder="••••••••" style={inputStyle} required
                value={loginData.password}
                onChange={e => setLoginData(prev => ({ ...prev, password: e.target.value }))}
              />
            </div>
          </div>
          <button type="submit" style={submitBtnStyle}>Sign In</button>
          <div style={{ marginTop: '1rem', textAlign: 'center' }}>
            <button type="button" onClick={() => setAuthMode('reset')} style={linkBtnStyle}>Forgot Password?</button>
            <span style={{ margin: '0 0.5rem', color: '#ccc' }}>|</span>
            <button type="button" onClick={() => setAuthMode('signup')} style={linkBtnStyle}>Create Account</button>
          </div>
        </form>
      )}

      {authMode === 'signup' && (
        <form onSubmit={handleSignup}>
          <div style={{ marginBottom: '1.2rem' }}>
            <label style={labelStyle}>Full Name</label>
            <div style={inputRowStyle}>
              <User size={20} color="#888" />
              <input type="text" placeholder="John Doe" style={inputStyle} required
                value={signupData.name}
                onChange={e => setSignupData(prev => ({ ...prev, name: e.target.value }))}
              />
            </div>
          </div>
          <div style={{ marginBottom: '1.2rem' }}>
            <label style={labelStyle}>Email Address</label>
            <div style={inputRowStyle}>
              <Mail size={20} color="#888" />
              <input type="email" placeholder="your@email.com" style={inputStyle} required
                value={signupData.email}
                onChange={e => setSignupData(prev => ({ ...prev, email: e.target.value }))}
              />
            </div>
          </div>
          <div style={{ marginBottom: '1.2rem' }}>
            <label style={labelStyle}>Phone Number</label>
            <div style={inputRowStyle}>
              <Phone size={20} color="#888" />
              <input type="tel" placeholder="+91-1234567891" style={inputStyle} required
                value={signupData.phone}
                onChange={e => setSignupData(prev => ({ ...prev, phone: e.target.value }))}
              />
            </div>
          </div>
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={labelStyle}>Password</label>
            <div style={inputRowStyle}>
              <Lock size={20} color="#888" />
              <input type="password" placeholder="••••••••" style={inputStyle} required
                value={signupData.password}
                onChange={e => setSignupData(prev => ({ ...prev, password: e.target.value }))}
              />
            </div>
          </div>
          <button type="submit" style={submitBtnStyle}>Create Account</button>
          <div style={{ marginTop: '1rem', textAlign: 'center' }}>
            <span style={{ color: '#666' }}>Already have an account? </span>
            <button type="button" onClick={() => setAuthMode('login')} style={linkBtnStyle}>Sign In</button>
          </div>
        </form>
      )}

      {authMode === 'reset' && (
        <form onSubmit={handlePasswordReset}>
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={labelStyle}>Email Address</label>
            <div style={inputRowStyle}>
              <Mail size={20} color="#888" />
              <input type="email" placeholder="your@email.com" style={inputStyle} required
                value={resetEmail}
                onChange={e => setResetEmail(e.target.value)}
              />
            </div>
          </div>
          <button type="submit" style={submitBtnStyle}>Send Reset Link</button>
          <div style={{ marginTop: '1rem', textAlign: 'center' }}>
            <button type="button" onClick={() => setAuthMode('login')} style={linkBtnStyle}>Back to Login</button>
          </div>
        </form>
      )}
    </div>
  </div>
);

// ─── Page: Detect ─────────────────────────────────────────────────────────────
const DetectionPage = ({ uploadedImage, analyzing, detectionResult, scanHistory, handleImageUpload, downloadReport, setCurrentPage }) => (
  <div style={{ minHeight: '100vh', background: 'linear-gradient(180deg,#F0F8FF,#E6F3FF)', padding: '3rem 2rem' }}>
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '2.5rem', fontWeight: 800, color: theme.darkText, marginBottom: '0.4rem' }}>Brain Tumor Detection</h1>
      <p style={{ color: '#666', fontSize: '1.05rem', marginBottom: '2rem' }}>Upload your MRI, CT, or X-ray for AI analysis</p>
      <div style={{ display: 'grid', gridTemplateColumns: uploadedImage ? '1fr 1fr' : '1fr', gap: '2rem' }}>
        <div style={{ background: 'white', borderRadius: '20px', padding: '2.5rem', boxShadow: '0 4px 20px rgba(0,0,0,0.08)' }}>
          <h3 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '1.5rem', color: theme.darkText }}>Upload Scan</h3>
          <label style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '3rem', border: '3px dashed #088395', borderRadius: '16px', cursor: 'pointer', background: 'rgba(8,131,149,0.03)' }}>
            <Upload size={60} color={theme.secondary} strokeWidth={1.5} />
            <p style={{ fontSize: '1.15rem', fontWeight: 600, color: theme.primary, marginTop: '1rem' }}>Click to Upload</p>
            <p style={{ color: '#666', marginTop: '0.4rem', fontSize: '0.9rem' }}>JPG, PNG, JPEG, DICOM</p>
            <input type="file" accept=".jpg,.jpeg,.png,.dcm" onChange={handleImageUpload} style={{ display: 'none' }} />
          </label>
          {uploadedImage && (
            <div style={{ marginTop: '1.5rem' }}>
              <p style={{ fontWeight: 600, marginBottom: '0.75rem', color: theme.darkText }}>Uploaded Image:</p>
              <img src={uploadedImage} alt="Scan" style={{ width: '100%', borderRadius: '12px' }} />
            </div>
          )}
        </div>

        {uploadedImage && (
          <div style={{ background: 'white', borderRadius: '20px', padding: '2.5rem', boxShadow: '0 4px 20px rgba(0,0,0,0.08)' }}>
            <h3 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '1.5rem', color: theme.darkText }}>Analysis Results</h3>
            {analyzing ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '3rem', gap: '1rem' }}>
                <Activity size={64} color={theme.secondary} />
                <p style={{ fontSize: '1.15rem', fontWeight: 600, color: theme.primary }}>Analyzing scan…</p>
              </div>
            ) : detectionResult && (
              <div>
                <div style={{ background: detectionResult.detected ? 'rgba(231,76,60,0.08)' : 'rgba(7,188,12,0.08)', border: `2px solid ${detectionResult.detected ? theme.danger : theme.success}`, borderRadius: '12px', padding: '1.2rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  {detectionResult.detected ? <AlertCircle size={38} color={theme.danger} /> : <CheckCircle size={38} color={theme.success} />}
                  <div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 700, color: detectionResult.detected ? theme.danger : theme.success }}>
                      {detectionResult.detected ? 'Tumor Detected' : 'No Tumor Detected'}
                    </div>
                    <div style={{ color: '#666', fontSize: '0.9rem' }}>Confidence: {detectionResult.confidence}%</div>
                  </div>
                </div>
                {detectionResult.detected && (
                  <>
                    <p style={{ fontSize: '0.85rem', color: '#666', fontWeight: 600, marginBottom: '0.3rem' }}>Tumor Type</p>
                    <p style={{ fontSize: '1.1rem', fontWeight: 600, color: theme.darkText, marginBottom: '1rem' }}>{detectionResult.type}</p>
                    <p style={{ fontSize: '0.85rem', color: '#666', fontWeight: 600, marginBottom: '0.4rem' }}>Severity</p>
                    <span style={{ padding: '0.4rem 1rem', borderRadius: '8px', fontWeight: 600, color: 'white', background: detectionResult.severity === 'Severe' ? theme.danger : detectionResult.severity === 'Moderate' ? theme.warning : theme.success, display: 'inline-block', marginBottom: '1rem' }}>{detectionResult.severity}</span>
                  </>
                )}
                <p style={{ fontSize: '0.85rem', color: '#666', fontWeight: 600, marginBottom: '0.3rem' }}>Recommendation</p>
                <p style={{ color: theme.darkText, lineHeight: 1.6, marginBottom: '1.5rem' }}>{detectionResult.recommendation}</p>
                <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                  <button onClick={downloadReport} style={{ flex: 1, background: theme.primary, color: 'white', border: 'none', padding: '0.9rem', borderRadius: '10px', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                    <Download size={18} /> Download Report
                  </button>
                  {detectionResult.detected && (
                    <button onClick={() => setCurrentPage('doctors')} style={{ flex: 1, background: theme.secondary, color: 'white', border: 'none', padding: '0.9rem', borderRadius: '10px', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                      <Stethoscope size={18} /> Find Doctor
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {scanHistory.length > 0 && (
        <div style={{ background: 'white', borderRadius: '20px', padding: '2.5rem', marginTop: '2rem', boxShadow: '0 4px 20px rgba(0,0,0,0.08)' }}>
          <h3 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '1.5rem', color: theme.darkText }}>Scan History</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(200px,1fr))', gap: '1rem' }}>
            {scanHistory.map(s => (
              <div key={s.id} style={{ border: '1px solid #E0E0E0', borderRadius: '12px', padding: '0.9rem' }}>
                {s.image ? (
                  <img src={s.image} alt="scan" style={{ width: '100%', height: '130px', objectFit: 'cover', borderRadius: '8px', marginBottom: '0.5rem' }} />
                ) : (
                  <div style={{ width: '100%', height: '130px', borderRadius: '8px', marginBottom: '0.5rem', background: 'linear-gradient(135deg,#EAF6F9,#D6EEF5)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: theme.secondary, fontWeight: 600 }}>
                    Stored Scan
                  </div>
                )}
                <div style={{ fontSize: '0.82rem', color: '#888' }}>{s.date}</div>
                <div style={{ fontWeight: 600, color: s.result.detected ? theme.danger : theme.success, fontSize: '0.88rem' }}>
                  {s.result.detected ? 'Tumor Detected' : 'No Tumor'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  </div>
);

// ─── Page: Doctors ────────────────────────────────────────────────────────────
const DoctorsPage = () => (
  <div style={{ minHeight: '100vh', background: 'linear-gradient(180deg,#F0F8FF,#E6F3FF)', padding: '3rem 2rem' }}>
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '2.5rem', fontWeight: 800, color: theme.darkText, marginBottom: '0.4rem' }}>Brain Specialist Contacts</h1>
      <p style={{ color: '#666', fontSize: '1.05rem', marginBottom: '1.8rem' }}>Manual doctor contact details are shown below.</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(320px,1fr))', gap: '1.5rem' }}>
          {mockDoctors.map(d => (
            <div key={d.id} style={{ background: 'white', borderRadius: '16px', padding: '2rem', boxShadow: '0 4px 20px rgba(0,0,0,0.08)' }}>
              <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.2rem' }}>
                <div style={{ fontSize: '2rem', background: 'linear-gradient(135deg,#088395,#05BFDB)', borderRadius: '12px', width: '72px', height: '72px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, color: 'white', fontWeight: 700 }}>
                  {d.name?.charAt(0) || 'D'}
                </div>
                <div>
                  <div style={{ fontSize: '1.15rem', fontWeight: 700, color: theme.darkText }}>{d.name}</div>
                  <div style={{ color: theme.secondary, fontWeight: 600, fontSize: '0.88rem', margin: '0.2rem 0 0.4rem' }}>{d.specialization}</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><Star size={14} color="#F1C40F" fill="#F1C40F" /><span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{d.rating}</span></div>
                </div>
              </div>
              {[
                [Activity, `${d.experience} yrs exp`],
                [Building2, d.hospital],
                [Phone, d.contact],
                [Mail, d.email],
                [MapPin, [d.city, d.state].filter(Boolean).join(', ')],
              ].map(([Icon, txt], i) => (
                <div key={i} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.45rem' }}>
                  <Icon size={15} color="#888" /><span style={{ fontSize: '0.88rem', color: '#555' }}>{txt}</span>
                </div>
              ))}
              <div style={{ margin: '0.8rem 0', display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                {(d.availability || []).map((day, i) => <span key={i} style={{ padding: '0.28rem 0.65rem', background: 'rgba(8,131,149,0.1)', color: theme.secondary, borderRadius: '6px', fontSize: '0.8rem', fontWeight: 600 }}>{day}</span>)}
              </div>
            </div>
          ))}
        </div>
    </div>
  </div>
);

// ─── Page: Hospitals ──────────────────────────────────────────────────────────
const HospitalsPage = () => (
  <div style={{ minHeight: '100vh', background: 'linear-gradient(180deg,#F0F8FF,#E6F3FF)', padding: '3rem 2rem' }}>
    <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '2.5rem', fontWeight: 800, color: theme.darkText, marginBottom: '0.4rem' }}>Nearby Brain Hospitals</h1>
      <p style={{ color: '#666', fontSize: '1.05rem', marginBottom: '1.8rem' }}>Showing a simple hospital map only.</p>
      <div style={{ background: 'white', borderRadius: '20px', padding: '1rem', boxShadow: '0 4px 20px rgba(0,0,0,0.08)' }}>
        <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: theme.darkText, marginBottom: '1rem' }}>Hospital Map</h3>
        <iframe
          title="nearby-brain-hospitals-map"
          src={buildMapEmbedUrl({
            query: 'brain hospitals in Jaipur, Rajasthan',
          })}
          style={{ width: '100%', height: '520px', border: 0, borderRadius: '14px' }}
          loading="lazy"
        />
      </div>
    </div>
  </div>
);

// ─── Page: Book Appointment ───────────────────────────────────────────────────
// eslint-disable-next-line no-unused-vars
const BookAppointmentPage = ({ selectedDoctor, appointmentData, setAppointmentData, handleBookAppointment, setCurrentPage }) => (
  <div style={{ minHeight: '100vh', background: 'linear-gradient(180deg,#F0F8FF,#E6F3FF)', padding: '3rem 2rem' }}>
    <div style={{ maxWidth: '750px', margin: '0 auto' }}>
      <button onClick={() => setCurrentPage('doctors')} style={{ background: 'transparent', border: 'none', color: theme.secondary, fontWeight: 600, cursor: 'pointer', marginBottom: '1rem', fontSize: '1rem' }}>← Back</button>
      <div style={{ background: 'white', borderRadius: '20px', padding: '2.5rem', boxShadow: '0 4px 20px rgba(0,0,0,0.08)' }}>
        <h2 style={{ fontSize: '1.8rem', fontWeight: 700, color: theme.darkText, marginBottom: '0.3rem' }}>Book Appointment</h2>
        <p style={{ color: '#666', marginBottom: '1.8rem' }}>with {selectedDoctor?.name}</p>
        <div style={{ background: 'rgba(8,131,149,0.07)', padding: '1.2rem', borderRadius: '12px', display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1.8rem' }}>
          <div style={{ fontSize: '2rem', background: 'linear-gradient(135deg,#088395,#05BFDB)', borderRadius: '10px', width: '58px', height: '58px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 700 }}>{selectedDoctor?.name?.charAt(0) || 'D'}</div>
          <div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: theme.darkText }}>{selectedDoctor?.name}</div>
            <div style={{ color: theme.secondary, fontWeight: 600, fontSize: '0.88rem' }}>{selectedDoctor?.specialization}</div>
          </div>
        </div>
        <form onSubmit={handleBookAppointment}>
          <div style={{ marginBottom: '1.3rem' }}>
            <label style={labelStyle}>Preferred Date</label>
            <input type="date" required value={appointmentData.date}
              onChange={e => setAppointmentData(prev => ({ ...prev, date: e.target.value }))}
              style={{ ...inputStyle, padding: '0.85rem 1rem', border: '2px solid #E0E0E0', borderRadius: '10px', width: '100%' }}
            />
          </div>
          <div style={{ marginBottom: '1.3rem' }}>
            <label style={labelStyle}>Preferred Time</label>
            <select required value={appointmentData.time}
              onChange={e => setAppointmentData(prev => ({ ...prev, time: e.target.value }))}
              style={{ ...inputStyle, padding: '0.85rem 1rem', border: '2px solid #E0E0E0', borderRadius: '10px', width: '100%' }}
            >
              <option value="">Select time slot</option>
              {['09:00 AM', '10:00 AM', '11:00 AM', '02:00 PM', '03:00 PM', '04:00 PM'].map(t => <option key={t}>{t}</option>)}
            </select>
          </div>
          <div style={{ marginBottom: '1.3rem' }}>
            <label style={labelStyle}>Appointment Type</label>
            <div style={{ display: 'flex', gap: '1rem' }}>
              {['in-person', 'online'].map(type => (
                <label key={type} style={{ flex: 1, padding: '0.85rem', borderRadius: '10px', cursor: 'pointer', textAlign: 'center', fontWeight: 600, border: `2px solid ${appointmentData.type === type ? theme.secondary : '#E0E0E0'}`, background: appointmentData.type === type ? 'rgba(8,131,149,0.08)' : 'white' }}>
                  <input type="radio" name="appt-type" value={type} checked={appointmentData.type === type} onChange={e => setAppointmentData(prev => ({ ...prev, type: e.target.value }))} style={{ marginRight: '0.4rem' }} />
                  {type === 'in-person' ? '🏥 In-Person' : '🌐 Online'}
                </label>
              ))}
            </div>
          </div>
          <div style={{ marginBottom: '1.8rem' }}>
            <label style={labelStyle}>Symptoms / Reason</label>
            <textarea required value={appointmentData.symptoms}
              onChange={e => setAppointmentData(prev => ({ ...prev, symptoms: e.target.value }))}
              placeholder="Describe your symptoms…"
              style={{ ...inputStyle, padding: '0.85rem 1rem', border: '2px solid #E0E0E0', borderRadius: '10px', width: '100%', minHeight: '100px', resize: 'vertical' }}
            />
          </div>
          <button type="submit" style={{ ...submitBtnStyle, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
            <Calendar size={20} /> Confirm Appointment
          </button>
        </form>
      </div>
    </div>
  </div>
);

// ─── Page: Appointments ───────────────────────────────────────────────────────
const AppointmentsPage = ({ appointments, setCurrentPage }) => (
  <div style={{ minHeight: '100vh', background: 'linear-gradient(180deg,#F0F8FF,#E6F3FF)', padding: '3rem 2rem' }}>
    <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '2.5rem', fontWeight: 800, color: theme.darkText, marginBottom: '0.4rem' }}>My Appointments</h1>
      <p style={{ color: '#666', fontSize: '1.05rem', marginBottom: '2rem' }}>Manage your scheduled consultations</p>
      {appointments.length === 0 ? (
        <div style={{ background: 'white', borderRadius: '20px', padding: '4rem 2rem', textAlign: 'center', boxShadow: '0 4px 20px rgba(0,0,0,0.08)' }}>
          <Calendar size={60} color="#CCC" style={{ margin: '0 auto 1rem' }} />
          <h3 style={{ fontSize: '1.4rem', fontWeight: 700, color: theme.darkText, marginBottom: '0.5rem' }}>No Appointments Yet</h3>
          <p style={{ color: '#666', marginBottom: '1.5rem' }}>Book your first consultation with our specialists</p>
          <button onClick={() => setCurrentPage('doctors')} style={{ background: theme.primary, color: 'white', border: 'none', padding: '0.9rem 2rem', borderRadius: '10px', fontWeight: 600, cursor: 'pointer' }}>Find Doctors</button>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '1.5rem' }}>
          {appointments.map(apt => (
            <div key={apt.id} style={{ background: 'white', borderRadius: '16px', padding: '2rem', boxShadow: '0 4px 20px rgba(0,0,0,0.08)', display: 'grid', gridTemplateColumns: '1fr auto', gap: '1.5rem', alignItems: 'center' }}>
              <div>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1rem' }}>
                  <div style={{ fontSize: '2rem', background: 'linear-gradient(135deg,#088395,#05BFDB)', borderRadius: '10px', width: '54px', height: '54px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 700 }}>{apt.doctor.name?.charAt(0) || 'D'}</div>
                  <div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 700, color: theme.darkText }}>{apt.doctor.name}</div>
                    <div style={{ color: theme.secondary, fontSize: '0.88rem', fontWeight: 600 }}>{apt.doctor.specialization}</div>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
                  <span style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', color: '#555', fontSize: '0.9rem' }}><Calendar size={14} color="#888" />{apt.date}</span>
                  <span style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', color: '#555', fontSize: '0.9rem' }}><Clock size={14} color="#888" />{apt.time}</span>
                  <span style={{ padding: '0.28rem 0.7rem', background: 'rgba(8,131,149,0.1)', color: theme.secondary, borderRadius: '6px', fontSize: '0.83rem', fontWeight: 600 }}>{apt.type === 'online' ? '🌐 Online' : '🏥 In-Person'}</span>
                </div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', alignItems: 'flex-end' }}>
                <span style={{ padding: '0.35rem 0.85rem', borderRadius: '8px', fontWeight: 600, fontSize: '0.85rem', background: 'rgba(241,196,15,0.15)', color: '#d4a600' }}>{apt.status}</span>
                <button style={{ background: 'transparent', color: theme.danger, border: `2px solid ${theme.danger}`, padding: '0.45rem 0.9rem', borderRadius: '8px', fontWeight: 600, cursor: 'pointer', fontSize: '0.85rem' }}>Cancel</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  </div>
);

// ─── Page: Profile ────────────────────────────────────────────────────────────
const ProfilePage = ({ user }) => (
  <div style={{ minHeight: '100vh', background: 'linear-gradient(180deg,#F0F8FF,#E6F3FF)', padding: '3rem 2rem' }}>
    <div style={{ maxWidth: '750px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '2.5rem', fontWeight: 800, color: theme.darkText, marginBottom: '2rem' }}>My Profile</h1>
      <div style={{ background: 'white', borderRadius: '20px', padding: '2.5rem', marginBottom: '2rem', boxShadow: '0 4px 20px rgba(0,0,0,0.08)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', marginBottom: '2rem', paddingBottom: '1.5rem', borderBottom: '2px solid #F0F0F0' }}>
          <div style={{ width: '88px', height: '88px', borderRadius: '50%', background: 'linear-gradient(135deg,#088395,#05BFDB)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '2.2rem', color: 'white', fontWeight: 700 }}>
            {user?.name?.charAt(0)}
          </div>
          <div>
            <div style={{ fontSize: '1.75rem', fontWeight: 700, color: theme.darkText }}>{user?.name}</div>
            <div style={{ color: '#888', marginTop: '0.2rem' }}>Member since {new Date().toLocaleDateString()}</div>
          </div>
        </div>
        {[[Mail, 'Email', user?.email], [Phone, 'Phone', user?.phone]].map(([Icon, lbl, val], i) => (
          <div key={i} style={{ marginBottom: '1.2rem' }}>
            <label style={labelStyle}>{lbl}</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.85rem 1rem', background: '#F8F9FA', borderRadius: '10px' }}>
              <Icon size={17} color="#888" /><span style={{ color: theme.darkText }}>{val}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  </div>
);

// ─── NavBar ───────────────────────────────────────────────────────────────────
const NavBar = ({ isLoggedIn, setCurrentPage, handleLogout }) => (
  <nav style={{ background: 'linear-gradient(135deg,#0A4D68,#088395)', padding: '1rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', boxShadow: '0 4px 20px rgba(8,131,149,0.3)', position: 'sticky', top: 0, zIndex: 1000 }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
      <Brain size={30} color="#05BFDB" strokeWidth={2.5} />
      <span style={{ color: 'white', fontSize: '1.4rem', fontWeight: 700 }}>NeuroDetect AI</span>
    </div>
    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
      {isLoggedIn ? (
        <>
          {[['home', 'Home'], ['detect', 'Scan'], ['doctors', 'Doctors'], ['hospitals', 'Hospitals'], ['appointments', 'Appointments'], ['profile', 'Profile']].map(([pg, lbl]) => (
            <button key={pg} onClick={() => setCurrentPage(pg)} style={navBtnStyle}>{lbl}</button>
          ))}
          <button onClick={handleLogout} style={{ ...navBtnStyle, background: '#E74C3C' }}>Logout</button>
        </>
      ) : (
        <button onClick={() => setCurrentPage('auth')} style={navBtnStyle}>Login / Sign Up</button>
      )}
    </div>
  </nav>
);

// ═══════════════════════════════════════════════════════════════════
// MAIN APP — state only, rendering delegated to page components above
// ═══════════════════════════════════════════════════════════════════
const BrainTumorDetectionApp = () => {
  const [currentPage, setCurrentPage] = useState('home');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [authMode, setAuthMode] = useState('login');
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [signupData, setSignupData] = useState({ name: '', email: '', password: '', phone: '' });
  const [resetEmail, setResetEmail] = useState('');
  const [uploadedImage, setUploadedImage] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [detectionResult, setDetectionResult] = useState(null);
  const [currentScanId, setCurrentScanId] = useState(null);
  const [scanHistory, setScanHistory] = useState([]);
  const [appointments, setAppointments] = useState([]);

  const fetchProfile = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/profile`, { headers: getAuthHeaders() });
      setUser(response.data.user);
      setIsLoggedIn(true);
    } catch {
      localStorage.removeItem('token');
      setUser(null);
      setIsLoggedIn(false);
    }
  };

  const fetchAppointments = async () => {
    if (!localStorage.getItem('token')) return;
    try {
      const response = await axios.get(`${API_BASE_URL}/api/appointments`, { headers: getAuthHeaders() });
      setAppointments(response.data);
    } catch (error) {
      console.error('Failed to fetch appointments', error);
    }
  };

  const fetchScans = async () => {
    if (!localStorage.getItem('token')) return;
    try {
      const response = await axios.get(`${API_BASE_URL}/api/scans`, { headers: getAuthHeaders() });
      const scans = response.data.map(scan => ({
        id: scan._id,
        date: scan.scan_date,
        image: null,
        imagePath: scan.image_path,
        result: normalizeDetectionResult(scan.detection_result),
      }));
      setScanHistory(scans);
    } catch (error) {
      console.error('Failed to fetch scans', error);
    }
  };

  useEffect(() => {
    if (localStorage.getItem('token')) {
      fetchProfile();
      fetchAppointments();
      fetchScans();
    }
  }, []);

  const handleLogin = async e => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth/login`, loginData);
      const { access_token, user: loggedInUser } = response.data;
      localStorage.setItem('token', access_token);
      setUser(loggedInUser);
      setIsLoggedIn(true);
      fetchAppointments();
      fetchScans();
      setCurrentPage('home');
      setLoginData({ email: '', password: '' });
    } catch (error) {
      alert(error.response?.data?.error || 'Login failed');
    }
  };

  const handleSignup = async e => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth/signup`, signupData);
      const { access_token, user: createdUser } = response.data;
      localStorage.setItem('token', access_token);
      setUser(createdUser);
      setIsLoggedIn(true);
      setAppointments([]);
      setScanHistory([]);
      setCurrentPage('home');
      setSignupData({ name: '', email: '', password: '', phone: '' });
    } catch (error) {
      alert(error.response?.data?.error || 'Signup failed');
    }
  };

  const handlePasswordReset = async e => {
    e.preventDefault();
    try {
      await axios.post(`${API_BASE_URL}/api/auth/reset-password`, { email: resetEmail });
      alert(`Reset link sent to ${resetEmail}`);
      setAuthMode('login');
      setResetEmail('');
    } catch (error) {
      alert(error.response?.data?.error || 'Password reset failed');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsLoggedIn(false);
    setUser(null);
    setAppointments([]);
    setScanHistory([]);
    setCurrentScanId(null);
    setDetectionResult(null);
    setUploadedImage(null);
    setCurrentPage('home');
  };

  const handleImageUpload = async e => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onloadend = async () => {
      setUploadedImage(reader.result);
      setAnalyzing(true);
      setDetectionResult(null);
      setCurrentScanId(null);
      try {
        const formData = new FormData();
        formData.append('image', file);
        const response = await axios.post(`${API_BASE_URL}/api/analyze`, formData, {
          headers: {
            ...getAuthHeaders(),
            'Content-Type': 'multipart/form-data',
          },
        });
        const normalizedResult = normalizeDetectionResult(response.data.result);
        setDetectionResult(normalizedResult);
        setCurrentScanId(response.data.scan_id);
        await fetchScans();
      } catch (error) {
        alert(error.response?.data?.error || 'Image analysis failed');
      } finally {
        setAnalyzing(false);
      }
    };
    reader.readAsDataURL(file);
  };

  const downloadReport = async () => {
    if (!currentScanId) {
      alert('No scan report available yet.');
      return;
    }
    try {
      const response = await axios.get(`${API_BASE_URL}/api/scans/${currentScanId}/report`, {
        headers: getAuthHeaders(),
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = `brain_scan_report_${currentScanId}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      alert(error.response?.data?.error || 'Report download failed');
    }
  };

  const pages = {
    home: <HomePage isLoggedIn={isLoggedIn} setCurrentPage={setCurrentPage} />,
    auth: <AuthPage authMode={authMode} setAuthMode={setAuthMode}
      loginData={loginData} setLoginData={setLoginData}
      signupData={signupData} setSignupData={setSignupData}
      resetEmail={resetEmail} setResetEmail={setResetEmail}
      handleLogin={handleLogin} handleSignup={handleSignup}
      handlePasswordReset={handlePasswordReset} />,
    detect: <DetectionPage uploadedImage={uploadedImage} analyzing={analyzing}
      detectionResult={detectionResult} scanHistory={scanHistory}
      handleImageUpload={handleImageUpload}
      downloadReport={downloadReport}
      setCurrentPage={setCurrentPage} />,
    doctors: <DoctorsPage />,
    hospitals: <HospitalsPage />,
    appointments: <AppointmentsPage appointments={appointments} setCurrentPage={setCurrentPage} />,
    profile: <ProfilePage user={user} />,
  };

  return (
    <div style={{ fontFamily: 'Inter, sans-serif' }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
        * { box-sizing: border-box; }
        button:hover { opacity: 0.9; }
        input:focus, textarea:focus, select:focus { border-color: #088395 !important; outline: none; }
      `}</style>
      <NavBar isLoggedIn={isLoggedIn} setCurrentPage={setCurrentPage} handleLogout={handleLogout} />
      {pages[currentPage] || pages['home']}
    </div>
  );
};

export default BrainTumorDetectionApp;

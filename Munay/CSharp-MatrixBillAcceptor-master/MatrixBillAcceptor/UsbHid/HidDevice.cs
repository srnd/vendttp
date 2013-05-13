using System;
using System.IO;
using System.Text;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;

namespace MatrixBillAcceptor.UsbHid
{
    internal abstract class HidDevice : Win32Usb, IDisposable
    {
        private FileStream m_oFile;
		private int m_nInputReportLength;
		private int m_nOutputReportLength;
		private IntPtr m_hHandle;

        public event EventHandler OnDeviceRemoved;
        public int OutputReportLength
        {
            get
            {
                return m_nOutputReportLength;
            }
        }
        public int InputReportLength
        {
            get
            {
                return m_nInputReportLength;
            }
        }
        public virtual InputReport CreateInputReport()
        {
            return null;
        }

        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }

        protected virtual void Dispose(bool bDisposing)
        {
            try
            {
                if (bDisposing)	// if we are disposing, need to close the managed resources
                {
                    if (m_oFile != null)
                    {
                        m_oFile.Close();
                        m_oFile = null;
                    }
                }
                if (m_hHandle != IntPtr.Zero)	// Dispose and finalize, get rid of unmanaged resources
                {

                    CloseHandle(m_hHandle);
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine(ex.ToString());
            }
        }

		private void Initialise(string strPath)
		{
            m_hHandle = CreateFile(strPath, GENERIC_READ | GENERIC_WRITE, 0, IntPtr.Zero, OPEN_EXISTING, FILE_FLAG_OVERLAPPED, IntPtr.Zero);

            if ( m_hHandle != InvalidHandleValue || m_hHandle == null)
			{
				IntPtr lpData;
				if (HidD_GetPreparsedData(m_hHandle, out lpData))
				{
                    try
                    {
                        HidCaps oCaps;
                        HidP_GetCaps(lpData, out oCaps);
                        m_nInputReportLength = oCaps.InputReportByteLength;
                        m_nOutputReportLength = oCaps.OutputReportByteLength;

                        m_oFile = new FileStream(new SafeFileHandle(m_hHandle, false), FileAccess.Read | FileAccess.Write, m_nInputReportLength, true);

                        BeginAsyncRead();                    
                    }
                    catch (Exception)
                    {
                        throw HidDeviceException.GenerateWithWinError("Failed to get the detailed data from the hid.");
                    }
					finally
					{
						HidD_FreePreparsedData(ref lpData);
					}
				}
				else
				{
					throw HidDeviceException.GenerateWithWinError("GetPreparsedData failed");
				}
			}
			else
			{
				m_hHandle = IntPtr.Zero;
				throw HidDeviceException.GenerateWithWinError("Failed to create device file");
			}
		}
        private void BeginAsyncRead()
        {
                byte[] arrInputReport = new byte[m_nInputReportLength];
                m_oFile.BeginRead(arrInputReport, 0, m_nInputReportLength, new AsyncCallback(ReadCompleted), arrInputReport);
        }
        protected void ReadCompleted(IAsyncResult iResult)
        {
            byte[] arrBuff = (byte[])iResult.AsyncState;
            try
            {
                m_oFile.EndRead(iResult);
                try
                {
					InputReport oInRep = CreateInputReport();
					oInRep.SetData(arrBuff);
                    HandleDataReceived(oInRep);
                }
                finally
                {
                    BeginAsyncRead();
                }                
            }
            catch(IOException) // Device removed
            {
                HandleDeviceRemoved();
                if (OnDeviceRemoved != null)
                {
                    OnDeviceRemoved(this, new EventArgs());
                }
                Dispose();
            }
        }

        protected void Write(OutputReport oOutRep)
        {
            try
            {
                m_oFile.Write(oOutRep.Buffer, 0, oOutRep.BufferLength);
            }
            catch (IOException)
            {
                throw new HidDeviceException("Could not write to the device: too short to previous write or device was removed.");
            }
			catch(Exception exx)
			{
                Console.WriteLine(exx.ToString());	
			}
        }

		protected virtual void HandleDataReceived(InputReport oInRep)
		{
		}

		protected virtual void HandleDeviceRemoved()
		{
		}

		private static string GetDevicePath(IntPtr hInfoSet, ref DeviceInterfaceData oInterface)
		{
			uint nRequiredSize = 0;
			if (!SetupDiGetDeviceInterfaceDetail(hInfoSet, ref oInterface, IntPtr.Zero, 0, ref nRequiredSize, IntPtr.Zero))
			{
                DeviceInterfaceDetailData oDetail = new DeviceInterfaceDetailData();
                if (Marshal.SizeOf(typeof(IntPtr)) == 8)
                {
                    oDetail.Size = 8;
                }
                else
                {
                    oDetail.Size = 5;
                }

				if (SetupDiGetDeviceInterfaceDetail(hInfoSet, ref oInterface, ref oDetail, nRequiredSize, ref nRequiredSize, IntPtr.Zero))
				{
					return oDetail.DevicePath;
				}
			}
			return null;
		}

		public static HidDevice FindDevice(int nVid, int nPid, Type oType)
        {
            string strPath = string.Empty;
			string strSearch = string.Format("vid_{0:x4}&pid_{1:x4}", nVid, nPid);
            Guid gHid = HIDGuid;
            IntPtr hInfoSet = SetupDiGetClassDevs(ref gHid, null, IntPtr.Zero, DIGCF_DEVICEINTERFACE | DIGCF_PRESENT);
            try
            {
                DeviceInterfaceData oInterface = new DeviceInterfaceData();
                oInterface.Size = Marshal.SizeOf(oInterface);
                int nIndex = 0;
                while (SetupDiEnumDeviceInterfaces(hInfoSet, 0, ref gHid, (uint)nIndex, ref oInterface))
                {
                    string strDevicePath = GetDevicePath(hInfoSet, ref oInterface);
                    if (strDevicePath.IndexOf(strSearch) >= 0)
                    {
                        HidDevice oNewDevice = (HidDevice)Activator.CreateInstance(oType);
                        oNewDevice.Initialise(strDevicePath);
                        return oNewDevice;
                    }
                    nIndex++;
                }
            }
            catch(Exception ex)
            {
                throw HidDeviceException.GenerateError(ex.ToString());
            }
            finally
            {
                SetupDiDestroyDeviceInfoList(hInfoSet);
            }
            // No device found.
            return null;
        }
    }
}

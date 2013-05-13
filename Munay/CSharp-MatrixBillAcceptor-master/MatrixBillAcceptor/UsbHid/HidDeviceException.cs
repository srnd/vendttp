using System;
using System.Text;
using System.Runtime.InteropServices;

namespace MatrixBillAcceptor.UsbHid
{
    internal class HidDeviceException : ApplicationException
    {
        public HidDeviceException(string strMessage) : base(strMessage) { }

        public static HidDeviceException GenerateWithWinError(string strMessage)
        {
            return new HidDeviceException(string.Format("Msg:{0} WinEr:{1:X8}", strMessage, Marshal.GetLastWin32Error()));
        }

        public static HidDeviceException GenerateError(string strMessage)
        {
            return new HidDeviceException(string.Format("Msg:{0}", strMessage));
        }
    }
}

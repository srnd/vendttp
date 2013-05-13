using System;
using System.Collections.Generic;
using System.Text;

namespace MatrixBillAcceptor.UsbHid
{
    internal class SpecifiedOutputReport : OutputReport
    {
        public SpecifiedOutputReport(HidDevice oDev) : base(oDev) {

        }

        public bool SendData(byte[] data)
        {
            byte[] arrBuff = Buffer;
            for (int i = 0; i < arrBuff.Length; i++)
            {
                arrBuff[i] = data[i];
            }

            if (arrBuff.Length < data.Length)
            {
                return false;
            }
            else
            {
                return true;
            }
        }
    }
}

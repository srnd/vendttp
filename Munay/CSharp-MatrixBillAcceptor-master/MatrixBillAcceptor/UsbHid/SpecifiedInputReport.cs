using System;
using System.Collections.Generic;
using System.Text;

namespace MatrixBillAcceptor.UsbHid
{
    internal class SpecifiedInputReport : InputReport
    {
        private byte[] arrData;

        public SpecifiedInputReport(HidDevice oDev) : base(oDev)
		{

		}

        public override void ProcessData()
        {
            this.arrData = Buffer;
        }

        public byte[] Data
        {
            get
            {
                return arrData;
            }
        }
    }
}

using System;

namespace MatrixBillAcceptor.UsbHid
{
	internal abstract class Report
	{
		private byte[] m_arrBuffer;
		private int m_nLength;

		public Report(HidDevice oDev)
		{
			
		}

		protected void SetBuffer(byte[] arrBytes)
		{
			m_arrBuffer = arrBytes;
			m_nLength = m_arrBuffer.Length;
		}

		public byte[] Buffer
		{
			get{return m_arrBuffer;}
            set{this.m_arrBuffer = value; }
		}
		public int BufferLength
		{
			get
			{
				return m_nLength;
			}
		}
	}
    internal abstract class OutputReport : Report
	{
		public OutputReport(HidDevice oDev) : base(oDev)
		{
			SetBuffer(new byte[oDev.OutputReportLength]);
		}
	}
    internal abstract class InputReport : Report
	{
		public InputReport(HidDevice oDev) : base(oDev)
		{
		}
		public void SetData(byte[] arrData)
		{
			SetBuffer(arrData);
			ProcessData();
		}
		public abstract void ProcessData();
	}
}

import CasesSection from './components/Cases/CasesSection'
import {RunTimeInfoModal} from './components/Modals/RunTimeInfoModal'
import RunInfoSection from './components/RunInfo/RunInfoSection'
import SummarySection from './components/Summary/SummarySection'
import {DetailsButtonModal} from './components/Modals/DetailsButtonModal'

export const ReportView = ({reportData}) => {
  return (
    <div>
      <div className='container p-4'>
        <RunInfoSection runInfo={reportData.runInfo}/>
        <SummarySection reportData={reportData}/>
        <CasesSection reportData={reportData}/>
      </div>
      {/*<RunTimeInfoModal reportData={reportData}/>*/}
      {/*<DetailsButtonModal reportData={reportData}/>*/}
    </div>
  )
}

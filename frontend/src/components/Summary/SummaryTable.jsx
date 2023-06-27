import ImplementationRow from './ImplementationRow'

const SummaryTable = ({reportData}) => {
  return (
    <table className='table table-sm table-hover'>
      <thead>
      <tr>
        <th
          colSpan={2}
          rowSpan={2}
          scope='col'
          className='text-center align-middle'
        >
          implementation
        </th>
        <th colSpan={1} className='text-center'>
          <span className='text-muted'>cases ({reportData.cases.size})</span>
        </th>
        <th colSpan={3} className='text-center'>
          <span className='text-muted'>tests ({reportData.totalTests})</span>
        </th>
        <th colSpan={1}></th>
      </tr>
      <tr>
        <th scope='col' className='text-center'>
          errors
        </th>
        <th scope='col' className='table-bordered text-center'>
          skipped
        </th>
        <th
          scope='col'
          className='table-bordered text-center details-required'
        >
          <div className='hover-details details-desc text-center'>
            <p>
              failed
              <br/>
              <span>
                  implementation worked successfully but got the wrong answer
                </span>
            </p>
            <p>
              errored
              <br/>
              <span>
                  implementation crashed when trying to calculate an answer
                </span>
            </p>
          </div>
          unsuccessful
        </th>
        <th scope='col'></th>
      </tr>
      </thead>
      <tbody className='table-group-divider'>
      {Array.from(reportData.implementations.values()).map((implementation, index) => (
        <ImplementationRow
          cases={reportData.cases}
          implementation={implementation}
          key={index}
          index={index}
        />
      ))}
      </tbody>
      <tfoot>
      <tr>
        <th scope='row' colSpan={2}>
          total
        </th>
        <td className='text-center'>{reportData.erroredCases}</td>
        <td className='text-center'>{reportData.skippedTests}</td>
        <td className='text-center details-required'>
          {reportData.unsuccessfulTests + reportData.erroredTests}
          <div className='hover-details text-center'>
            <p>
              <b>failed</b>: {reportData.unsuccessfulTests}
            </p>
            <p>
              <b>errored</b>: {reportData.erroredTests}
            </p>
          </div>
        </td>
        <td></td>
      </tr>
      </tfoot>
    </table>
  )
}

export default SummaryTable

import './ImplementationRow.css'
import {InfoCircleFill} from 'react-bootstrap-icons'

const ImplementationRow = ({implementation, index}) => {
  return (
    <tr>
      <th scope='row'>
        <a href={implementation.metadata.homepage ?? implementation.metadata.issues}>
          {implementation.metadata.name}
        </a>
        <small className='text-muted'>{' ' + implementation.metadata.language}</small>
      </th>
      <td>
        <small className='font-monospace text-muted'>
          {implementation.metadata.version ?? ''}
        </small>
        <button
          className='btn border-0'
          data-bs-toggle='modal'
          data-bs-target={`#implementation-${index}-runtime-info`}
        >
          <InfoCircleFill/>
        </button>
      </td>

      <td className='text-center'>{implementation.erroredCases}</td>
      <td className='text-center'>{implementation.skippedTests}</td>
      <td className='text-center details-required'>
        {implementation.unsuccessfulTests + implementation.erroredTests}
        <div className='hover-details text-center'>
          <p>
            <b>failed</b>:{implementation.unsuccessfulTests}
          </p>
          <p>
            <b>errored</b>:{implementation.erroredTests}
          </p>
        </div>
      </td>

      <td>
        <button
          type='button'
          className='btn btn-sm btn-primary'
          data-bs-toggle='modal'
          data-bs-target={`#implementation-${index}-details`}
        >
          Details
        </button>
      </td>
    </tr>
  )
}

export default ImplementationRow
